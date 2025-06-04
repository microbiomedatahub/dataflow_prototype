import sys

def load_target_ids(target_file):
    target_ids = set()
    with open(target_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                target_ids.add(line.split('\t')[0])  # 1列目をIDとみなす
    return target_ids

def filter_tsv_by_ids(input_tsv, output_tsv, target_ids):
    with open(input_tsv, 'r', encoding='utf-8') as fin, \
         open(output_tsv, 'w', encoding='utf-8') as fout:
        for line in fin:
            if line.split('\t', 1)[0] in target_ids:
                fout.write(line)

# 使用方法: python script.py input.tsv target_ids.tsv output.tsv
if __name__ == "__main__":
    """
    assembly_summary_*.txtを先頭のカラムのIDでフィルターしIDのリストに含まれる行だけをファイルに出力するスクリプト。
    クエリとなるIDリストはtarget_ids.tsvのように保存する。
    使用例:
    python filter_by_genome.py assembly_summary_refseq.txt target_ids.tsv output.tsv
    """
    if len(sys.argv) != 4:
        print("Usage: python script.py <input.tsv> <target_ids.tsv> <output.tsv>")
        sys.exit(1)

    input_file = sys.argv[1]
    target_file = sys.argv[2]
    output_file = sys.argv[3]

    ids = load_target_ids(target_file)
    filter_tsv_by_ids(input_file, output_file, ids)
