# データの新規作成・更新手順

データや解析データの取得およびMdatahub環境へのデータ配置、オントロジーマッピングなどアノテーションおよびデータ形式変換、検索データのElasticsearchデータ投入について記載する

## セットアップ 
https://github.com/microbiomedatahub/docker-microbiome-datahub/README.md に従う

## データセット毎の新規データ取得、変換および投入
#### mag-insdc
1. 最新のbioproject.xml取得
    - ```wget https://ddbj.nig.ac.jp/public/ddbj_database/bioproject/bioproject.xml```
    - 現在の本番は、```/work1/mdatahub/repos/dataflow_prototype/bioproject.xml``` のシンボリックリンクのsourceが最新データ

```
[mdb_dev@cs9 dataflow_prototype]$ pwd
/work1/mdatahub/repos/dataflow_prototype
[mdb_dev@cs9 dataflow_prototype]$ ls -la bioproject.xml
lrwxrwxrwx. 1 mdb_dev mdb_dev 23  6月 12  2023 bioproject.xml -> bioproject-20230612.xml
```

2. 対象となるProjectサブセットのIDリストを取得 `create_project_accessions.rb `
3. プロジェクト毎に各種データ（bioprojext.xml、biosample IDs、biosampleset.xml）を取得 `bioproject_mget.rb`
4. Elasticsearch bulk APIで投入用のLine-delimited JSON形式ファイルを生成 `create_indexes.rb`
5. Elasticsearchへの全長jsonlのbulk import
    - Elasticsearchは100MBを超えるJSONファイルのbulk importができないため、このサイズを超えるデータは分割してインポートします。
```
mkdir bulk_import
bash bin/split.sh #TODO:対象ファイルと出力先の修正
curl -XDELETE http://localhost:9200/bioproject 
bash bin/bulk_import.sh
```

#### gnm-refseq
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

### test
テストデータを利用した動作確認は https://github.com/microbiomedatahub/docker-microbiome-datahub/README.md に従う。以下のテストデータ変換方法は古いので、要動作確認
```
ruby bin/create_indexes.rb testdata
```
