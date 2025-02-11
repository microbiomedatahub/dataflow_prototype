# 1. 環境セットアップ
https://github.com/microbiomedatahub/docker-microbiome-datahub/README.md に従う。index_template/* を利用したElasticsearchのtemplate設定は、...


# 2. Genomeデータの新規作成・更新手順
ゲノムデータの準備からElasticsearchデータ投入方法を記載する

### 2-1. 準備
assembly_summaryファイルを配置後、setup_genome.pyを実行することでゲノム毎のデータが配置される

dfast, dfast-qc, bac2feature, mbgdについては、...

```
cd  /work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/
wget -O assembly_summary_refseq-20250116.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt
ln -s assembly_summary_refseq-20250116.txt assembly_summary_refseq.txt
wget -O assembly_summary_genbank-20250116.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt
ln -s assembly_summary_genbank-20250116.txt assembly_summary_refseq.txt

python3 bin/setup_genome.py insdc
python3 bin/setup_genome.py refseq

```

### 2-2. 実行方法
genomeインデックスのレコードgenome.jsonを生成し、JSONLを生成せず直接Elasticsearchに投入される

読み込むファイルコマンドライン引数で渡して下記のように実行する（デフォルトでINSDC-MAGのファイルが指定されて、ステージング環境にデータが投入される。）

```
python3 bin/create_index_genome.py -s /work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt
```

---

## 3. Projectの新規データ取得、変換および投入
*** プロジェクトにつていは、あとで整理する***


### 1. 最新のbioproject.xml取得
    - ```wget https://ddbj.nig.ac.jp/public/ddbj_database/bioproject/bioproject.xml```
    - 現在の本番は、```/work1/mdatahub/repos/dataflow_prototype/bioproject.xml``` のシンボリックリンクのsourceが最新データ

```
[mdb_dev@cs9 dataflow_prototype]$ pwd
/work1/mdatahub/repos/dataflow_prototype
[mdb_dev@cs9 dataflow_prototype]$ ls -la bioproject.xml
lrwxrwxrwx. 1 mdb_dev mdb_dev 23  6月 12  2023 bioproject.xml -> bioproject-20230612.xml
```

### 2. 対象となるProjectサブセットのIDリストを取得 `create_project_accessions.rb `
### 3. プロジェクト毎に各種データ（bioprojext.xml、biosample IDs、biosampleset.xml）を取得 `bioproject_mget.rb`
### 4. Elasticsearch bulk APIで投入用のLine-delimited JSON形式ファイルを生成 

#### Project `create_index_project.rb`

```
        * 仕様：bioprojectxml2json.rbとbioproject_plus.rbの統合
        * 仕様：bioproject_accessions (102176件) かつ `/work1/mdatahub/public/project/` にデータ取得されたaccessionsがindex対象
        * working directory: /work1/mdatahub/repos/dataflow_prototype
        * 入力: bioproject.xml (bioproject-20230612.xml)
        * 入力: project_accessions (project_accessions-20230612)
        * 入力: /work1/mdatahub/public/project/
            * ln -s /work1/mdatahub/public/project で対応
        * 出力: mdatahub_index_project.jsonl (mdatahub_index_project-20230612.jsonl)
    * ESに投入（6/14 Done）
        * `/work1/mdatahub/repos/dataflow_prototype/mdatahub_index_project-20230612.jsonl`
            * 102174/102176件
            * PRJDB11833, PRJDB15377, 2件分足りないのは公開ファイルとEntrez Directが叩くAPIのタイムラグ？
    * TODO: 入力データ配置後にcreate_indexes.rbスクリプト拡張後、ES投入（次回の合宿？）
        * genome_count、has_analysis
            * [bioproject_plus.rb#L489-L505](https://github.com/microbiomedatahub/dataflow_prototype/blob/main/bin/bioproject_plus.rb#L489-L505) のあたり
        * data_sizeの反映
        * genome index作成
        * ES投入
```


### 5. Elasticsearchへの全長jsonlのbulk import

Elasticsearchは100MBを超えるJSONファイルのbulk importができないため、このサイズを超えるデータは分割してインポートします。

- JSONLの分割
- split.shを実行しJSONLを分割しますが、入力ファイルと出力ディレクトリがハードコードされているため修正します
```
cd dataflow_prototype
vi bin/split.sh

split -l $splitlen -a 3 -d /work1/mdatahub/app/dataflow_prototype/{jsonl path} ../bulk_import/{日付}/{prefix ex. project_jsonl_part_}
```

- ディレクトリを作り分割スクリプトを実行

```
mkdir bulk_import/ $(date +%Y%m%d)
bash bin/split.sh 
```

```
mkdir bulk_import
bash bin/split.sh #TODO:対象ファイルと出力先の修正
curl -XDELETE http://localhost:9200/bioproject 
bash bin/bulk_import.sh
```

### 6. メタゲノム解析の系統組成データをplotly JSONに変換する

- 系統組成データ可視化の概要
- Runごとの系統組成データ（例 ERR0000_1.fastq.sam.mapped..）をBioProjectごとにPlotlyのstacked chartに形式に変換し読み込みJSONデータを書き出します。
- チャートのx軸はRunからBioSapleに変換したIDが利用されます。同じBioSampleがサンプルに割り当てられた場合、サンプル名にチャート内indexを表すsuffixが振られます。
- RunからBioProjectへの変換、RunからBioSampleへの変換はTogoIDを利用しています。

- 仮想環境の設定
  - cd plotly
  - source venv/bin/activate　

- 変換スクリプトの実行
  - python kraken2plotlyjson.py -i <入力するファイルを配置したディレクトリのパス>　[-o <出力するファイルの親ディレクトリ>]

- 実行例
- 
```
$ python kraken2plotlyjson.py -i /work1/mdatahub/private/megap -o /work1/mdatahub/public/project
```

### スクリプト 利用確認
以下は、プロジェクトデータ作成時に利用しているスクリプト群。不要な古いスクリプトは bin-oldに移動。
* create_project_accessions.rb # (2)
* bioproject_mget.rb # (3)
* create_index_project.rb　# (4)-a
* create_index_genome.rb # (4)-b
* bulk_import.sh #(5)
* split.sh #(5)?
* plotly/tsv2plotlyjson.py #(6) 

* mdatahub.rb # scriptから参照
* lib_bioprojectxml2json.rb # scriptから参照
