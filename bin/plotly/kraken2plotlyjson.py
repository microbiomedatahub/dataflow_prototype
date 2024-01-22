# encoding: utf-8
import pandas as pd
import numpy as np
import csv
import os
import glob
from typing import List
import plotly.express as px
import argparse
import re

from sra_id_convert import togoid_run2biosample, togoid_run2bioproject
# デフォルトの出力パスの共通部分
output_path = "/work1/mdatahub/public/project"
# togoidに問い合わせるIDのchunk size
chunksize = 500

# 入力ファイルパス,出力ファイルパスはコマンドラインoption -i, -oで指定する
# cwd = os.getcwd()
parser = argparse.ArgumentParser()
# --inputオプションはソースファイルを納めたディレクトリを指定する
parser.add_argument('-i', '--input', type=str, required=True)
# --outputオプションはJSONを書き出すディレクトリの共通部分を指定する.プロジェクトの個別のURLは
# プロジェクト名から自動的にスクリプト内で作成する
parser.add_argument('-o', '--output', type=str)
# krakin2形式ファイルの拡張子を指定する。デフォルトはcsv
parser.add_argument('-e', '--extension', type=str, default='csv')
args = parser.parse_args()
input_path = args.input
file_extension = args.extension
if args.output is None:
    output_path = output_path
else:
    output_path = args.output

# kraken2 reportのヘッダ
headers = ['count', 'superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain'
           'filename', 'sig_name', 'sig_md5', 'total_counts']
# 出力する階級をリストで指定
ranks = ["phylum", "family", "genus", "species"]

def plotlyjson_formatter(d: pd.DataFrame, filenname:str, rank: str) -> dict:
    """
    DFをplotly用のjsonに変換する
    :return:
    """
    # Todo: DFをplotly用のjsonに変換する
    colors = px.colors.qualitative.T10
    # plotly
    
    #df = df.astype({'count': 'int64'})
    fig = px.bar(d, 
                x = d.index,
                y = [c for c in d.columns],
                template = 'ggplot2',
                color_discrete_sequence = colors
                )

    fig.update_layout(
    title = 'Phlogenetic compositions', 
        xaxis_title="Samples",
        yaxis_title="Composition(%)",
        legend_title="Genus",
        font=dict(
            family="sans-serif",
            size=12,
        )
    )
    #fig.show()
    # fig.write_json(filenname, pretty=True)
    export2jsonfile(fig,filenname, rank)


def list2df(lst: List[list], rank:str, sample_name) -> pd.DataFrame:
    """
    [[taxonomy name, count],,]形式のlistを
    plotly用にサンプルをconcatする直前までの整形したDataFrameに変換する。
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
    d = df_all[s.sort_values(ascending=False).index[:]]
    return d


def get_file_names(input_path) -> list:
    """_summary_
    指定したディレクトリ以下のファイル名を取得する
    Args:
        input_path (_type_): _description_
    Returns:
        list: ディレクトリに含まれる全tsvファイルのリスト
    """
    
    # 子階層の任意のディレクトリ名にマッチするワイルドカードを追加
    file_names = glob.glob(input_path + '/*/*.' + file_extension)
    return file_names


def get_run_id(file_name) -> str:
    """_summary_
    ファイル名からrun_idを取得する。
    想定するファイル名はrun id + _n.fastq.sam.mapped.bam...txtのような文字列なので
    ファイル名先頭のアルファベット＋数字分部分を利用する。
        file_name (_type_): _description_
    Returns:
        str: run_id
    """
    # input_path=子階層/ファイル名なのでファイル名部分のみに修正
    file_name = file_name.split("/")[-1]
    # 三頭のアルファベット＋数字分部分を取得
    run_id = re.findall(r'^[a-zA-Z0-9]+', file_name)
    return run_id[0]


def export2jsonfile(fig:px.bar, bioproject:str, rank:str):
    """_summary_
    - プロジェクト毎にまとめたplotly用系統組成をJSONファイルを書き出す
    - プロジェクト名のディレクトリを作成しそのディレクトリに各ランクのファイルを配置する
    """
    # プロジェクト名のディレクトリを作成する > projectディレクトリは有るものと考える
    """
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    """
    # jsonファイルに書き出し
    path = acc2path(bioproject)
    print("path: ", path, "project: ", bioproject)
    # Todo: ディレクトリの存在確認。無い場合は作成する
    try:
        fig.write_json(f"{path}/analysis_{rank}.json", pretty=True)
    except FileNotFoundError:
        os.makedirs(path)
        fig.write_json(f"{path}/analysis_{rank}.json", pretty=True)


def acc2path(acc:str) -> str:
    """_summary_
    BioProjectのIDを受け取り、数字部分を6桁に０埋めしたプロジェクトのファイルパスを返す
    Args:
        acc (str): BioProject ID
    Returns:
        path(str): 個別のファイルパスパス
    """
    m = re.match(r"^(PRJ[A-Z]+)([0-9]+)$", acc)
    acc_prefix = m[1]
    acc_num = m[2]
    dir_name = acc_num.zfill(6)
    path = f"{output_path}/{acc_prefix}/{dir_name[0:3]}/{acc_prefix}{dir_name}"
    return path


def chunks(lst, n):
    """_summary_
    引数として与えられたリストをサイズnに分割しyeildする
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    """__summary__
    - kraken2 report形式のファイルを読み込み、plotly用のjsonを書き出す
    - ファイル名の先頭にRUN IDつくので、このIDをBioProjectに変換してプロジェクトごとのjsonを書き出す
    - 各ファイルが一つのRUNの解析に相当するが、RUNをBioSampleに変換してbarchartのサンプル名として表示する
    """
    # ファイル名のリストを取得
    file_names = get_file_names(input_path)
    # パスから子階層をふくんだファイル名を取得する
    # file_names = [f.split("/")[-1] for f in file_names if f.endswith(file_extension)]
    file_names = ["/".join(f.split("/")[-2:]) for f in file_names if f.endswith(file_extension)]
    run_list = []
    for file_name in file_names:
        # Todo: file_nameはパス名を含むので、パス名を除いたファイル名のみを取得する
        run_id = get_run_id(file_name)
        run_list.append(run_id)
    # run-bioprojectの関係リストを取得
    # run_bp_list = togoid_run2bioproject.run_bioproject(run_list)
    # Todo: chunksizeを指定して一度に読み込む行数を制限する
    run_bp_list = []
    for l in chunks(run_list, chunksize):
        run_bp_list.extend(togoid_run2bioproject.run_bioproject(l))
    # bioprojectでrun idをグループ化
    bp_nested_list = togoid_run2bioproject.convert_nested_bioproject_list(run_bp_list)
    # bioproject毎に組成データを読み込む（ネストしたそれぞれのリスト（run）に先頭の文字列が一致するファイルリストを作りファイルを読み込む）
    for k, v in bp_nested_list.items():
        # k: bioproject, v: run_id list
        # run idでfile_namesをフィルタリング（先頭の文字列がrun_id listに含まれるファイル名を取得）

        # "/45/DRR002467_2.fastq.term.fastq.sig.csv"のようなパスの途中にRUN IDが含まれる
        # "/"でsplitした二つ目の要素の先頭がRUN IDに一致するファイルを取得する
        # filtered_file_names = [f for f in file_names if f.startswith(tuple(v))]
        filtered_file_names = [f for f in file_names if f.split("/")[-1].startswith(tuple(v))]
        # prun idからrun:biosampleの辞書を作成. > filtered_file_namesはパス名を含むので、パス名を除く
        # run_list = [f.split("_")[0] for f in filtered_file_names]
        run_list = [re.split("_|/", f)[-2] for f in filtered_file_names]

        # todo: run_listがchunk_sizeを超える場合chunks()で分割して実行する
        sample_names = {}
        if len(run_list) < chunksize:
            sample_names = togoid_run2biosample.run_biosample(run_list)
        else:
            for l in chunks(run_list, chunksize):
                print("bioproject: ", k, "len: ", len(l))
                sample_names.update(togoid_run2biosample.run_biosample(l))

        for rank in ranks:
            dfs = []
            for i,f in enumerate(filtered_file_names):
                # kraken2形式のファイルを読み込み、組成テーブルを2Dリストとして取得する
                lst = read_kraken2report(input_path + "/" + f)
                lst_species = select_by_rank(lst, rank)
                sample_name = sample_names[run_list[i]]
                dfs.append(list2df(lst_species, rank, sample_name))
            df_con = concat_samples(dfs)
            plotlyjson_formatter(df_con, k, rank)


if __name__ == "__main__":
    main()
