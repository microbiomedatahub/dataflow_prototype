# データの新規作成・更新手順

データや解析データの取得およびMdatahub環境へのデータ配置、オントロジーマッピングなどアノテーションおよびデータ形式変換、検索データのElasticsearchデータ投入について記載する

## 環境セットアップ 
https://github.com/microbiomedatahub/docker-microbiome-datahub/README.md に従う。

## テストデータを利用した動作確認
https://github.com/microbiomedatahub/docker-microbiome-datahub/README.md に従う。以下のテストデータ変換方法は古いので、要動作確認。

```
ruby bin/create_indexes.rb testdata
```

## INSDC由来のProjectとMAGの新規データ取得、変換および投入

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

#### Genome `create_index_genome.rb`

```
```

### 5. Elasticsearchへの全長jsonlのbulk import

Elasticsearchは100MBを超えるJSONファイルのbulk importができないため、このサイズを超えるデータは分割してインポートします。
```
mkdir bulk_import
bash bin/split.sh #TODO:対象ファイルと出力先の修正
curl -XDELETE http://localhost:9200/bioproject 
bash bin/bulk_import.sh
```

### 6. メタゲノム解析の系統組成データをplotly JSONに変換する
- Runごとの系統組成データ（例 ERR0000_1.fastq.sam.mapped..）の配置されたディレクトリを指定しBioProjectごとにPlotlyのstacked chartに読み込むJSONデータを書き出します。
- チャートのx軸はRunからBioSapleに変換したIDが利用されます。同じBioSampleがサンプルに割り当てられた場合、サンプル名にチャート内indexを表すsuffixが振られます。
- RunからBioProjectへの変換、RunからBioSampleへの変換はTogoIDを利用しています。
- 入力ファイルパス,出力ファイルパスはコマンドラインoption -i, -oで指定。出力ファイルのパスは省略可能。省略した場合入力ファイルと同じディレクトリにプロジェクト毎ディレクトリが作られる。

```
$ python tsv2plotlyjson.py -i 入力ファイルのパス -o 出力パス
```


---
### スクリプト 利用確認
* create_project_accessions.rb # (2)
* bioproject_mget.rb # (3)
* create_index_project.rb　# (4)-a
* create_index_genome.rb # (4)-b
* bulk_import.sh #(5)
* split.sh #(5)?
* plotly/tsv2plotlyjson.py #(6) 

### ESセットアップ

`要ドキュメント`

* index_template/*

#### script参照
* mdatahub.rb
* lib_bioprojectxml2json.rb

#### 動作未確認作業スクリプト
* mget_asm
* mget_asm_checkm
* mget_biosample_from_asm
* mget_asm_gi
* rebuild_directory_project.rb
* rebuild_directory_genome.rb
* mget
* mget_bioproject
* copy_MAGoutput_dfast_218655.rb
* copy_MAGoutput_dfastqc_218655.rb

---
## TODO

RefSeqリファレンスゲノムおよびMGnify由来のMAGについてはあとで更新する（2024-12-05）

### gnm-refseq
PGAPを使ってないいにしえのモデル微生物３件。全てのリファレンスゲノムは、強制的に、PRJNA224116のRefSeqエントリーに紐づけることにする
```
[tf@at044 ~]$ grep "assembly from type material" /lustre9/open/shared_data/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt |egrep "archaea|bacteria" |cut -f2 |sort |uniq -c
   21745 PRJNA224116
      1 PRJNA57675
      1 PRJNA57777
      1 PRJNA57799
```
1. PRJNA224116.xmlを取得
    - ```efetch -db bioproject -id PRJNA224116  -mode xml > PRJNA224116.xml```
2. GCF階層ディレクトリを作成して GCF Assembly Accesion毎にbiosampleエントリーのxmlを取得して配置。ID関係の最新情報は以下で取得可能。
```
grep "assembly from type material" /lustre9/open/shared_data/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt |egrep "archaea|bacteria" |cut -f1,3
```
3. dfastおよびdfast-qcの結果を配置
4. JSON変換と投入

### mag-mgnify
```
TBW
```

 ```
