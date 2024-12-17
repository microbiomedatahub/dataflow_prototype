import csv
import os
import glob
import re
import json
from typing import List, Dict
import pandas as pd
import argparse
import zipfile

from sra_id_convert import togoid_run2bioproject

# kraken2 reportのヘッダ
headers = ['count', 'superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain'
           'filename', 'sig_name', 'sig_md5', 'total_counts']
# 出力する階級をリストで指定
ranks = ["phylum", "class", "order", "family", "genus", "species"]
chunksize = 500


def get_args():
    parser = argparse.ArgumentParser(description="This script takes in a directory of kraken2 output files and creates a composition file for each project")
    # --inputオプションはソースファイルを納めたディレクトリを指定する
    parser.add_argument('-i', '--input', type=str, required=True)
    # --outputオプションはJSONを書き出すディレクトリの共通部分を指定する.プロジェクトの個別のURLは
    # プロジェクト名から自動的にスクリプト内で作成する
    parser.add_argument('-o', '--output', type=str)
    # kraken2形式の組成ファイルの拡張子を指定する。デフォルトはcsv
    parser.add_argument('-e', '--extension', type=str, default='csv')
    return parser.parse_args()


def get_file_list(input_path: str, file_extension: str) -> List[str]:
    """
    Get list of file in the input directory
    :param input_path:
    :return:
    """
    import os
    args = get_args()
    # 子階層の任意のディレクトリ名にマッチするワイルドカードを追加
    # file_names = glob.glob(input_path + '/*/*.' + file_extension)
    # 開発用のディレクトリ
    file_names = glob.glob(f'../sample/*.{args.extension}*')
    return file_names


def get_run_ids(file_name: str):
    """
    Get run ids from file names
    :return:
    """
    # input_path=子階層/ファイル名なのでファイル名部分のみに修正
    file_name = file_name.split("/")[-1]
    # 三頭のアルファベット＋数字分部分を取得
    run_id = re.findall(r'^[a-zA-Z0-9]+', file_name)
    return run_id[0]



def read_kraken2report(file_path: str) -> List[list]:
    """
    kraken2 reportファイル」を読みこんでlistを返す
    :return:
    """
    # 1. read kraken2 report and return as list
    with open(file_path, "r") as f:
        d = csv.reader(f, delimiter=",")
        # 先頭行はヘッダが返る
        rows = [row for row in d]
        return rows


def logs(project: str):
    """
    Write converted composition data to log file
    """
    with open("log.txt", "a") as f:
        f.write(f"{project} \n")


def chunks(lst, n):
    """
    引数として与えられたリストをサイズnに分割しyeildする
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def zip_list(output_path:str, compositions: List[Dict[str, List[list]]]):
    """
    # プロジェクト毎zipファイルを作成する場合の関数
    rankごとに別れた２次元リスト（系統組成テーブル）をzipしてファイル出力する

    """
    # 出力先ディレクトリの存在を確認し、無い場合は作成する
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    with zipfile.ZipFile(f"{output_path}/composition.zip", "w") as zf:
        for composition in compositions:
            rank = composition["rank"]
            list_data = composition["data"]
            csv_data = "\n".join(["\t".join(map(str, row)) for row in list_data])
            
            # CSV形式の文字列をバイナリデータに変換します
            binary_data = csv_data.encode('utf-8')
            # Zipファイルに二次元リストを追加します
            zf.writestr(rank + ".tsv", binary_data)


def write_list(output_path: str, compositions: List[Dict[str, List[list]]]):
    """
    rankごとに別れた２次元リスト（系統組成テーブル）をtsvファイルとして出力する
    """
    if not os.path.exists(output_path):
        # os.makedirsは再起的にディレクトリを作成するのでプロジェクトディレクトリのしたの
        # compositionsのディレクトリを指定する
        output_path = output_path + "/compositions/"
        os.makedirs(output_path)
    for composition in compositions:
        rank = composition["rank"]
        list_data = composition["data"]
        # ファイル名を作成
        file_name = output_path + rank + ".tsv"
        with open(file_name, "w") as f:
            for row in list_data:
                f.write("\t".join(map(str, row)) + "\n")



def select_by_rank(rows: list, rank: str) -> List[list]:
    """
    kraken2形式のテーブルのrowsからrankが引数で指定した値の行（count, taxonomy）だけを抽出して返す。
    rankの一致の判定は記述のある最も細分化されたrankが指定したrankかどうかを判定する。
    taxonomy nameはreportで付加されたprefixを除去して返す。
    :param rows:
    :param rank:
    :return:
    """
    # 空行を除去
    rows = [row for row in rows if len(row) > 0 ]
    # 引数で指定したrankのカラムの序数を取得する
    i = headers.index(rank)
    if i == -1:
        raise ValueError("rank is not found in headers")
    elif rank == "strain":
        # strainのカラムに値がある行を返す. strainとspeciesのカラムの序数をハードコードしている
        selected_rows = [row for row in rows if row[7] != "" and row[8] != ""]
    else:
        # 指定したrankのカラムに値があり、rankの次のカラムに値がない行を抽出する
        selected_rows = [row for row in rows if row[i] != "" and row[i+1] == ""]
    # taxonomy nameのprefixを除去、countとtaxonomy nameのみのリストを返す
    selected_rows = [[row[i].split("__")[1], int(row[0])] for row in selected_rows]
    # ヘッダ行を追加
    selected_rows.insert(0, [rank, ''])
    return selected_rows


def concat_samples(df_lst: List[pd.DataFrame]) -> pd.DataFrame:
    """
    複数のサンプルから得たDFを結合する
    :return:
    """
    # サンプルを結合する
    df_all = pd.concat(df_lst, axis=0)
    # 欠損値を0で埋める
    df_all.fillna(0, inplace=True)
    # 列ごとに合計値を算出しサンプル毎の合計値でDFをソートする
    s = df_all.sum()
    d = df_all[s.sort_values(ascending=False).index[:]]
    return d


def list2df(lst: List[list], rank:str, sample_name) -> pd.DataFrame:
    """
    [[taxonomy name, count],,]形式のlistを
    DataFrameに変換する。
    :param lst:
    :return:
    """
    df = pd.DataFrame(lst, columns=[rank, sample_name])

    # ヘッダ行を削除する
    df = df[1:]
    df[sample_name] = df[sample_name].astype(int)

    # rankのカラムをインデックスとする
    df = df.set_index(rank, drop=True)
    # DFを天地し行指向にデータを追加できるフォーマットに変換する
    df = df.T
    # カラムの値をカラムの合計値で割り%を算出する
    df = df.div(df.sum(axis=1), axis=0).mul(100)
    return df


def main():
    args = get_args()
    input_path = args.input
    # output_path = args.output
    extention = args.extension

    # 指定ディレクトリ内の全組成ファイル（ex. csv）を取得
    files = get_file_list(input_path, extention)
    # ファイルリストからrun idリストを生成
    run_list = [get_run_ids(f) for f in files]
    # run idからbioproject idを取得しrelationを作成
    run_bp_list = []
    for l in chunks(run_list, chunksize):
        run_bp_list.extend(togoid_run2bioproject.run_bioproject(l))
    # bioprojectでrun idをグループ化
    bp_nested_run_list = togoid_run2bioproject.convert_nested_bioproject_list(run_bp_list)

    # プロジェクトごとの組成データを作成
    for bp, run_lst in bp_nested_run_list.items():
        # run idとファイル名の先頭が一致するファイルのリストを取得
        filterd_files = [f for f in files if f.split("/")[-1].startswith(tuple(run_lst))]

        # rankごとの組成データを変換
        compositions = []
        for rank in ranks:
            dfs = []
            for i, f in enumerate(filterd_files):
                # kraken2形式のファイルを読み込み、組成テーブルを2Dリストとして取得する
                lst = read_kraken2report(input_path + "/" + f)
                # rankでフィルターする
                lst_species = select_by_rank(lst, rank)
                # sample_name = sample_names[run_list[i]]
                dfs.append(list2df(lst_species, rank, run_lst[i]))
            # dfsを結合する
            df_concat = concat_samples(dfs)
            df_concat = df_concat.T
            col_names = df_concat.columns.tolist()
            # indexの文字列（taxonomy）でDFをソートする
            df_concat = df_concat.sort_index()
            col_names.insert(0, "taxonomy")
            # DFを2Dリストに変換
            lst = [list(x) for x in df_concat.to_records().tolist()]
            # ヘッダ行を追加
            lst.insert(0, col_names)
            compositions.append({"rank": rank, "data": lst})

        # zipファイルに出力 << 処理の実行位置要検討
        #output_path = f"../sample/test/{bp}/"
        path_base = args.output
        project_name = bp
        project_prefix = project_name[0:5]
        project_number = project_name[5:]
        converted_project_number = project_number.zfill(6)
        output_path = f"{path_base}/{project_prefix}/{converted_project_number[0:3]}/{project_prefix}{converted_project_number}/"
        #zip_list(output_path,compositions)
        write_list(output_path, compositions)
        # ログに処理したプロジェクト名を追記
        logs(bp)


if __name__ == '__main__':
    main()

