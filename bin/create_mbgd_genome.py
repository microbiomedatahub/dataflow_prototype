import csv
import json
import os
import re
import datetime
import argparse
import urllib.request
from io import StringIO
from collections import Counter


def read_csv(file_path) -> list:
    """
    CSVファイルを読み込み、各行をリストに格納する
    """
    with open(file_path) as f:
        reader = csv.reader(f)
        data = [row[0].split('\t') for row in reader]
    return data


def read_ko(url) -> dict:
    """
    TXTファイルを読み込み、各行をリストに格納し先頭２要素をk:vとしたdictを返す
    """
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('utf-8')  # UTF-8でデコード（必要に応じて変更）
        text_io = StringIO(data)
        lines = []
        for line in text_io:
            lines.append(line.rstrip().split('\t'))

        data = {row[0]: row[1] for row in lines}
    return data


def read_description(file_path) -> list:
    """
    TSVファイルを読み込み先頭のIDをkeyとしてdescriptionをvalueとしたdictを返す
    """
    with open(file_path) as f:
        reader = csv.reader(f, delimiter='\t')
        data = {row[0]: row[1] for row in reader}
    return data


def create_output_directory(root_path, mag_id) -> str:
    """
    出力先のpathを生成する
    /hoge/hoge/public/genome/GCA/xxx
    ex. /hoge/hoge/public/genome/GCA/949/121/495/GCA_949121495.1
    ex. /hoge/hoge/public/genome/GCA/000/192/595/GCA_000192595.1
    /hoge/hoge/public/genome/GCF/xxx
    """
    mag_id_str = re.sub(r"[_.]", "", mag_id)
    mag_id_lst = [mag_id_str[i:i+3] for i in range(0, len(mag_id_str), 3)]
    output_path = f"{root_path}/{mag_id_lst[0]}/{mag_id_lst[1]}/{mag_id_lst[2]}/{mag_id_lst[3]}/{mag_id}/mgbd.json"
    return output_path
     

def main():
    """
    - MAG IDとortholog cluster IDの対応表を取得する。
    - MAGとortholog cluster IDの対応を集計しかつcluster idにKOをマッピングする。
    - 集計した結果を各MAGごとにディレクトリにJSONL形式で出力する。
    """
    # cl引数で指定する場合argparseのコメントを外す
    # parser = argparse.ArgumentParser(description='create_mbgd_genome')
    # parser.add_argument('--mags', '-m', help='mag-ortholog file path')
    # parser.add_argument('--ko', '-k', help='kegg orthology table url')
    #parser.add_argument('--output', '-o', help='output root directory')
    # args = parser.parse_args()
    mags_path = "../testdata/test_mbgd_cluster.txt" 
    ko_url = "https://mbgd.nibb.ac.jp/tmp/microbedb/mbgd_kegg_xref_default.txt"
    genome_root_path = "/public/genome"
    # clusterのdescriptinを追加
    description_path = "public/dev/mbgdcluster.tsv"

    # CSVファイルを読み込み、各行を辞書型に変換してリストに格納する
    mag_list = read_csv(mags_path)
    ko_map = read_ko(ko_url)
    # descrioption_mapは枝番を除いたclust idをkeyとするdict
    description_map = read_description(description_path)
    # MAGの1レコードごとの処理
    for mag in mag_list:
        # MAG IDをパースする
        mag_id  = "_".join(mag[0].split("_")[0:2])
        # cluster idをカウントする
        cluster_id = mag[1:]
        d = [{"id": k, "count": v, "ko": ko_map.get(k, ""), "description": description_map.get( f"{k:.0f}","")} 
             for k,v in Counter(cluster_id).items() if k != ""]
        # 出力先のディレクトリを作成し
        # マッピング結果をJSONL形式で出力する
        today = datetime.date.today()
        try:
            with open(create_output_directory(genome_root_path, mag_id), 'w') as f:
                json.dump(d, f, indent=4, ensure_ascii=False)
                # 出力したMAGは作業日のlogファイルにIDを追記する
            with open(f"{today}_mbgd_logs.txt", 'a') as log_f:
                log_f.write(f"{mag_id}\n")
        except FileNotFoundError as e:
            # ディレクトリが存在しない場合はerror logを出力する
            # TODO: logファイルの出力先を指定する
            with open(f"{today}_mbgd_errors.txt", 'a') as log_e:
                log_e.write(f"{mag_id} {e}\n")


if __name__ == '__main__':
    main()