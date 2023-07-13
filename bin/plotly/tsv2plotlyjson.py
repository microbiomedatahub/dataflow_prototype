import os
import glob
import pandas as pd
import numpy as np
import plotly.express as px
import re
import csv
import argparse

from sra_id_convert import togoid_run2biosample, togoid_run2bioproject

# 入力ファイルパス,出力ファイルパスはコマンドラインoption -i, -oで指定する
cwd = os.getcwd()
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default=cwd)
parser.add_argument('-o', '--output', type=str)   
args = parser.parse_args()
input_path = args.input
if args.output is None:
    output_path = input_path
else:
    output_path = args.output


def get_file_names(input_path) -> list:
    """_summary_
    指定したディレクトリ以下のファイル名を取得する
    Args:
        input_path (_type_): _description_
    Returns:
        list: ディレクトリに含まれる全tsvファイルのリスト
    """
    file_names = glob.glob(input_path + '/*.txt')
    return file_names

def create_df(file_name: list) -> pd.DataFrame:
    """
    ファイル名のリストを受け取り、各ファイルをデータフレームに読み込む
    処理途中のカラム名設定で、sra_id_convertを利用してrun->biosample変換を行う
    Args: 組成データのファイル名リスト
    """
    # dfはinput_path + ファイル名を引数として読み込む
    # ファイル名: file_name    
    # run id:
    # Run->BioSampleに変換
    run_ids = [f.split('.')[0] for f in file_name]
    run_ids = [f.split('_')[0] for f in  run_ids]

    # カラム名はrun idから変換したbiosample id# カラム名はrun idから変換したbiosample id
    # 重複を考慮しprefix追加する
    biosample_ids = togoid_run2biosample.run_biosample(run_ids)

    df_lst = []
    df = {}
    # 最初のプロジェクトのみとりあえず書き出す（後で全件に修正する）
    for i,d in enumerate(file_name):
        # ファイルをdfに読み込む・BioSampleを組成の列のカラム名にする
        # クラスは現状genus固定
        run_id = d.split('_')[0]
        bs = biosample_ids[run_id]
        df[i] = pd.read_table(f"{input_path}/{d}", names=['genus',bs])
        # インデックス設定
        df[i] = df[i].set_index('genus', drop=True)

        # 天地
        df[i] = df[i].T
        # リード数をトータル100としてレコード毎各サンプルの値を正規化する
        df[i] = df[i].div(df[i].sum(axis=1), axis=0).mul(100)
        df_lst.append(df[i])

    # 全サンプルをデータフレームに行方向にconcat。NaNが挿入されるので0で埋める
    df_all = pd.concat(df_lst, axis=0)
    df_all.fillna(0, inplace=True)

    # 列毎に全サンプルを加算しその値でソート
    s = df_all.sum()
    d = df_all[s.sort_values(ascending=False).index[:]]
    return d

def get_run_id(file_name) -> str:
    """_summary_
    ファイル名からrun_idを取得する。
    想定するファイル名はrun id + _n.fastq.sam.mapped.bam...txtのような文字列なので
    ファイル名先頭のアルファベット＋数字分部分を利用する。
        file_name (_type_): _description_
    Returns:
        str: run_id
    """
    run_id = re.findall(r'^[a-zA-Z0-9]+', file_name)
    return run_id[0]


def create_plot_json(bioproject:str, file_names:list):
    """_summary_
    projectごとのファイル名リストを受け取り、組成値のplotly用jsonを生成しファイル出力する
    Args:
        file_names (_type_): ファイル名リスト
    """
    d = create_df(file_names)
    colors = px.colors.qualitative.T10
    # plotly
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
    # fig.show()は実行しなくても影響ない
    # fig.show()
    # bioprojectディレクトリを作成
    path = output_path + f"/{bioproject}"
    os.mkdir(path)

    # jsonファイルに書き出し
    fig.write_json(f"{output_path}/{bioproject}/analysis.json", pretty=True)


def main() -> None:
    """
    1.ファイル名リストを取得しrun->bioprojectにID変換を行う
    2.bioproject毎組成（リード数絶対値） データを読み込む
    3.run->biosampleにカラム名の変換を行う
    4.plotly用jsonにを生成しファイルに出力する
    main()では
    Args:
        path (str): _description_
    """
    file_names = get_file_names(input_path)
    file_names = [f.split("/")[-1] for f in file_names if f.endswith('.txt')]
    run_list = []
    for file_name in file_names:
        # Todo: file_nameはパス名を含むので、パス名を除いたファイル名のみを取得する
        run_id = get_run_id(file_name)
        run_list.append(run_id)
    # run-bioprojectの関係リストを取得
    run_bp_list = togoid_run2bioproject.run_bioproject(run_list)
    # bioprojectでrun idをグループ化
    bp_nested_list = togoid_run2bioproject.convert_nested_bioproject_list(run_bp_list)
    # bioproject毎に組成データを読み込む（ネストしたそれぞれのリスト（run）に先頭の文字列が一致するファイルリストを作りファイルを読み込む）
    for k, v in bp_nested_list.items():
        # k: bioproject, v: run_id list
        # run idでfile_namesをフィルタリング（先頭の文字列がrun_id listに含まれるファイル名を取得）
        filtered_file_names = [f for f in file_names if f.startswith(tuple(v))]
        # plotlyjsonを生成しファイル出力（BioProjectをファイル名にしてディレクトリを作りディレクトリに設置）
        create_plot_json(k, filtered_file_names)


if __name__ == '__main__':
    main()