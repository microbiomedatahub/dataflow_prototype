from __future__ import annotations
import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, OrderedDict
from collections import OrderedDict as _OrderedDict


def read_ontology_map(path: str | Path) -> "OrderedDict[str, str]":
    """
    ontology_label.tsv を読み込んで、順序付きの {ontology_id: label} を返す。
    - 2列（id, label）。ヘッダー行の有無は自動判定。
    """
    path = Path(path)
    mapping: "OrderedDict[str, str]" = _OrderedDict()

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)

    if not rows:
        return mapping

    # ヘッダー自動判定
    head = rows[0]
    start_idx = 1 if (len(head) >= 2 and {"id", "label"} <= {h.strip().lower() for h in head[:2]}) else 0

    for row in rows[start_idx:]:
        if len(row) < 2:
            continue
        oid = row[0].strip()
        label = row[1].strip()
        if oid:
            mapping[oid] = label or oid  # ラベル欠損時はIDを代用
    return mapping


def read_sample_matrix(path: str | Path) -> Tuple[List[str], List[List[str]]]:
    """
    sample.tsv を行列として読み込む。
    戻り値: (rows[0] をヘッダーと解釈した場合の header, すべての行データ)
    - ヘッダーの有無はこの後のロジック側で判定するため、ここではただ返すだけ。
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)

    if not rows:
        return [], []
    return rows[0], rows


def is_truthy(x: str) -> bool:
    """
    '1','true','yes','on','t','y' などを True とみなす。
    """
    if x is None:
        return False
    s = str(x).strip().lower()
    return s in {"1", "true", "yes", "y", "t", "on"}


# DEP> create_output_directory は下に移動
def sample_out_dir(root: str | Path, sample_id: str) -> Path:
    """
    サンプルごとの出力ディレクトリを決める（必要なら好きなロジックに差し替え）。
    """
    return Path(root) / sample_id


def create_output_directory(root_path, mag_id) -> str:
    """
    出力先のpathを生成する
    ./public/genome/GCA/xxx
    ex. ./public/genome/GCA/949/121/495/GCA_949121495.1
    ex. ./public/genome/GCA/000/192/595/GCA_000192595.1
    """
    mag_id_str = re.sub(r"[_.]", "", mag_id)
    mag_id_lst = [mag_id_str[i:i+3] for i in range(0, len(mag_id_str), 3)]
    output_path = f"{root_path}/{mag_id_lst[0]}/{mag_id_lst[1]}/{mag_id_lst[2]}/{mag_id_lst[3]}/{mag_id}/module.json"
    return output_path


# ---------- 主要処理 ----------
def generate_jsons(
    ontology_tsv: str | Path,
    sample_tsv: str | Path,
    out_root: str | Path,
    #output_filename: str = "module.json",
) -> None:
    """
    - ontology_tsv: 2列（id, label）
    - sample_tsv: 1列目が sample_id、2列目以降がオントロジー列（ヘッダー名=オントロジーID でも可）
    - out_root/sample_id/ontologies.json に書き出す
    """
    ont_map = read_ontology_map(ontology_tsv)  # Ordered {id: label}
    ontology_ids_in_order = list(ont_map.keys())

    header_first_row, rows = read_sample_matrix(sample_tsv)
    if not rows:
        return

    # ヘッダー有無の判定
    # 実際のソースファイルは先頭3行にontologyのラベルを含むがそれらは事前に取り除いておくことを想定する
    # 条件: 2列目以降のヘッダーが "全て ont_map に含まれるID" ならヘッダーありとみなす
    has_header = False
    if header_first_row and len(header_first_row) >= 2:
        candidate_ids = [h.strip() for h in header_first_row[1:]]
        if candidate_ids and all(cid in ont_map for cid in candidate_ids):
            has_header = True

    # データ行の開始位置
    start_idx = 1 if has_header else 0

    # オントロジー列のID並び（ヘッダーがあればそれを優先、無ければ ont_map の順）
    ontology_id_columns: List[str]
    if has_header:
        ontology_id_columns = [h.strip() for h in rows[0][1:]]
    else:
        ontology_id_columns = ontology_ids_in_order

    # 列数の妥当性チェック（無ヘッダー時にズレていないか）
    expected_cols = 1 + len(ontology_id_columns)

    for r in rows[start_idx:]:
        if not r:
            continue
        # 足りない/多い列は丸める
        row = (r + [""] * expected_cols)[:expected_cols]

        sample_id = row[0].strip()
        if not sample_id:
            continue

        bits = row[1:]
        present_ontology_ids = [
            oid for oid, bit in zip(ontology_id_columns, bits) if is_truthy(bit)
        ]

        # 出力する {id, label} の配列を作成
        payload = [{"id": oid, "label": ont_map.get(oid, oid)} for oid in present_ontology_ids]

        # id属性の値でソート
        payload.sort(key=lambda x: x["id"])

        # 書き出し
        out_path_str = create_output_directory(out_root, sample_id)
        out_path = Path(out_path_str)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fw:
            json.dump(payload, fw, ensure_ascii=False, indent=2)


# ---------- CLI ----------
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Generate per-sample ontology JSON files from TSVs."
    )
    ap.add_argument("--ontology-tsv", required=True, help="Path to ModuleList_name.tsv  (id,label)")
    ap.add_argument("--sample-tsv", required=True, help="Path to maple_matrix.txt (sample matrix)")
    ap.add_argument("--out-root", required=True, help="Directory to write per-sample JSONs")
    # ファイル名はmodule.jsonに固定するためコメントアウト
    # ap.add_argument("--filename", default="ontologies.json", help="Output JSON filename per sample")
    args = ap.parse_args()

    # default値は
    # ontology-tsv: ModuleList_name.tsv
    # sample-tsv: maple_matrix.txt

    generate_jsons(
        ontology_tsv=args.ontology_tsv,
        sample_tsv=args.sample_tsv,
        out_root=args.out_root
        #output_filename="module.json",
    )
