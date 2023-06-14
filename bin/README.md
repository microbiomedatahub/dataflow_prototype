# bioprojectxml2json.rb

BioProject.xmlをjsonlファイルに変換します。

## 使い方
- 現状L:162に読み込むxmlのパスをハードコードしています。実際のパスに書き換えてください
- 出力するファイル名もL146にハードコードしています。必要であればこちらの書き換えもお願いします。
- "ruby bioprojectxml2json.rb" で実行します。

2023-06-14更新
- 引数で指定されたディレクトリ内のbioproject.xmlを入力ファイルとし、同じディレクトリ内にbioproject.jsonが出力されます。デフォルトはカレントディレクトリです。
- Classをlib_bioprojectxml2json.rbに移動し、外部ファイル化しました。

```
%ruby bin/bioprojectxml2json.rb testdata
bin/bioprojectxml2json.rb:11: warning: Ractor is experimental, and the behavior may change in future versions of Ruby! Also there are many implementation issues.
2023-06-14 11:18:25 +0900 Started
2 packages converted.
2023-06-14 11:18:25 +0900 Finished
```


# Elasticsearchへの全長jsonlのbulk import

Elasticsearchは100MBを超えるJSONファイルのbulk importができないため、このサイズを超えるデータは分割してインポートします。

- 分割作業用にjsonlをコピーします
- cd bulk_import
- source split.sh
- curl -XDELETE http://localhost:9200/bioproject 
- source bulk_import.sh