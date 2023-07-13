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

# メタゲノム解析の系統組成データをplotly JSONに変換する

- Runごとの系統組成データ（例 ERR0000_1.fastq.sam.mapped..）の配置されたディレクトリを指定しBioProjectごとにPlotlyのstacked chartに読み込むJSONデータを書き出します。
- チャートのx軸はRunからBioSapleに変換したIDが利用されます。同じBioSampleがサンプルに割り当てられた場合、サンプル名にチャート内indexを表すsuffixが振られます。
- RunからBioProjectへの変換、RunからBioSampleへの変換はTogoIDを利用しています。
- 入力ファイルパス,出力ファイルパスはコマンドラインoption -i, -oで指定。出力ファイルのパスは省略可能。省略した場合入力ファイルと同じディレクトリにプロジェクト毎ディレクトリが作られる。

## 使い方

 ```
$ python tsv2plotlyjson.py -i 入力ファイルのパス -o 出力パス

 ```