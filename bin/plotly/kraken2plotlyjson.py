# encoding: utf-8
import pandas as pd
import csv
from typing import List

# kraken2 reportのヘッダ
headers = ['count', 'superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain'
           'filename', 'sig_name', 'sig_md5', 'total_counts']


def plotlyjson_formatter(d: pd.DataFrame, rank: str) -> dict:
    """
    DFをplotly用のjsonに変換する
    :return:
    """
    # Todo: DFをplotly用のjsonに変換する
    pass


def list2df(lst: List[list], rank:str) -> pd.DataFrame:
    """
    [[taxonomy name, count],,]形式のlistを
    plotly用にサンプルをconcatする直前までの整形したDataFrameに変換する。
    :param lst:
    :return:
    """
    df = pd.DataFrame(lst)
    # 先頭行をカラム名にする.ヘッダを設定しヘッダ行を削除する
    df.columns = df.iloc[0]
    df = df[1:]
    # rank名のカラムをインデックスにする
    df = df.set_index(rank, drop=True)
    # DFを天地する
    df = df.T
    # カラムの値をカラムの合計値で割り%を算出する
    df = df.div(df.sum(axis=1), axis=0).mul(100)
    return df


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


def select_by_rank(rows: list, rank: str) -> List[list]:
    """
    rowsからその行の分類rankが引数で指定した値の行（count, taxonomy）だけを抽出して返す。
    rankの一致の判定は最も細分化されたrankが指定したrankかどうかを判定する。
    taxonomy nameはreportで付加されたprefixを除去して返す。
    :param rows:
    :param rank:
    :return:
    """
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
    df_all_sorted = df_all[s.sort_values(ascending=False).index[:]]
    return df_all_sorted


def main():
    test_reports = ["/Users/oec/Desktop/data/MDB/kraken2report_sample/out100.csv",
                    "/Users/oec/Desktop/data/MDB/kraken2report_sample/out100_copy1.csv"]
    # Todo: 開発上speciesでテストするが、s,g,f,oでDFをつくりJSONを書き出す
    rank = "species"
    dfs = []
    for i,f in enumerate(test_reports):
        lst = read_kraken2report(f)
        lst_species = select_by_rank(lst, "species")
        dfs.append(list2df(lst_species, rank))
    df = concat_samples(dfs)
    dct = plotlyjson_formatter(df, rank)


if __name__ == "__main__":
    main()