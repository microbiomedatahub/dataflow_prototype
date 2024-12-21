import argparse
import csv
import json


def tsv2dict(csv_file: str) -> dict:
    """
    tsvファイルを読み込み、各行をdictに格納する
    Returns:
        dict: 
    """
    d = {}
    with open (csv_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            d.update({row["MAG_ID"]: row })
    return d

class WriteJsonl:
    def __init__(self, output_file):
        self.output_file = output_file
    def write_jsonl(self, jsonl):
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(jsonl) + '\n')

def main():
    """
    Elasticsearchに投入する形式のjsonlを取得し
    追加テーブルのデータを取得した上で
    レコード中の指定するIDと突合しレコードに追加して
    再度jsonlを出力する
    """
    """
    parser = argparse.ArgumentParser(description='genome_add_phenotype')
    # 既存のjsonlファイルを指定
    parser.add_argument('jsonl', '--jsonl', '-j' help='file path')
    parser.add_argument('feature', '--feature', '-f',  help='file path')
    # 出力先のjsonlファイルを指定
    parser.add_argument('output', '--output', '-o', help='Index')
    args = parser.parse_args()
    b2f_file = args.feature
    jsonl_file = args.jsonl
    """
    b2f_file  = './mag_1000_B2F.txt'
    jsonl_file = './genome_jsonl_part_000'
    output_file = './genome_feature_part_000'
    phenotype_dict = tsv2dict(b2f_file)
    write_jsonl = WriteJsonl(output_file)
    
    # ローカルにおかれたjsonlファイルを取得
    with open(jsonl_file) as f:
        records = f.readlines()
        for i, record in enumerate(records):
            dct = json.loads(record)
            # 偶数行（index）の処理
            if i % 2 == 0:
                # そのまま出力
                write_jsonl.write_jsonl(dct)
 
            # 奇数行（header）の処理
            if i % 2 == 1:
                # 例えばidentifierを取得し、追加テーブルのデータを取得する場合
                mag_id = dct["identifier"]
                additional_data = get_additional_data(phenotype_dict, mag_id)
                dct.update(additional_data)
                # ヘッダ行とデータ本体のセットで処理を行う
                write_jsonl.write_jsonl(dct)



# mag_idで対応するbac2featureのデータを取得
def get_additional_data(phenotype, mag_id):
    d = phenotype.get(mag_id)
    if d:
        d.pop("MAG_ID")
        return {"_bac2feature": d}
    else:
        return {}


if __name__ == '__main__':
    main()
