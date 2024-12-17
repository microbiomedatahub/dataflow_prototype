# plotlyデータの生成と表示

## 概要

- kraken2plotlyjson.pyはkraken2出力形式の系統組成データファイルからplotly用JSONファイルを生成するツールです。
- 入力する系統組成ファイルは一つのディレクトリにまとめ、プログラムを呼び出す際にオプションでディレクトリのパスを指定します。
- RUN IDより変換したBioProject IDを利用して自動的にプロジェクトにデータをまとめるJSONデータを出力します（入力するファイル名にはRUN IDを先頭につけてください）。
- プロットに表示されるサンプル名はRUNをBioSampleに変換した値です。RUNからBioProject、BioSampleの変換はTogoIDを利用しています。

## 環境の設定

- plotly用JSONの生成はPythonの標準仮想環境モジュールのvenvを利用し仮想環境で処理することを想定しています。
- 以下コマンドで仮想環境を有効化します

```
$ cd <kraken2plotlyjson.pyの設置されたディレクトリ>
$ python3 -m venv venv
$ source venv/bin/activate
```
- 仮想環境を初めて利用する場合はpandas, plotly等のライブラリのインストールが必要です。 以下コマンドでライブラリをインストールします。

```
$ pip install -r requirements.txt
```

## 入力データについて

- kraken2形式の系統組成データを一つのディレクトリにまとめて設定してください。
- 1サンプル1ファイルでデータは記述します。ファイル名の先頭にはRUN IDを記載してください。

## plotly用JSONファイルの出力

- kraken形式の系統組成データを入力とし、プロジェクト単位でまとめた系統組成をplotlyで可視化する積層BarPlot用のJSONファイルを書き出します。
- 指定したディレクトリにkraken2形式のファイルをディレクトリに分けて配置します
- アプリケーションはディレクトリ内のファイルを再起的に収集しrun idを利用してプロジェクト単位にまとめて可視化用にJSONに変換します
- 変換されたJSONは自動的にJSONファイルとしてプロジェクトディレクトリに書き出されます
- 仮想環境の設定
  - cd plotly
  - source venv/bin/activate　
- 実行
  - python kraken2plotlyjson.py -i <入力するファイルを配置したディレクトリのパス>　

実行例
```
$ python kraken2plotlyjson.py -i /work1/mdatahub/private/megap
```


JSONはプロジェクト名のディレクトリに階級ごと（現在order, family, genus, speciesを設定している）書き出される。
```
├── PRJEB1786
│   ├── analysis_family.json
│   ├── analysis_genus.json
│   ├── analysis_order.json
│   └── analysis_species.json
├── PRJNA217052
│   ├── analysis_family.json
│   ├── analysis_genus.json
│   ├── analysis_order.json
│   └── analysis_species.json
```

## pltlyを利用した積み上げバーチャートの表示

以下の要素をHTMLに埋め込み表示します

```
<head>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.18.1.min.js" charset="utf-8"></script>

</head>
<body>
    <div id="myDiv" style="width:1000px;height:500px;"></div>
</body>
<script>
    // 静的なJSONファイルのパスを記述
    const jsonUrl = "./プロジェクト_ランク.json"
            d3.json(jsonUrl, function(error, data){
        if (error) return console.warn(error);
        let layout = {barmode: 'stack',legend:{traceorder:"normal"}};
        Plotly.newPlot('myDiv', data, layout)
    })

</script>
```

# 系統組成データのTSVファイル出力概要


keraken2composition.pyでは任意のディレクトリに保存されたkraken2形式の系統組成データを
プロジェクト/ランク毎にTSVファイル変換してzip圧縮します

## input形式

- 以下のようなヘッダを持ったkraken2の出力形式を持ったcsvファイルを入力として想定しています。


```
count,superkingdom,phylum,class,order,family,genus,species,strain,filename,sig_name,sig_md5,total_counts
```

### 出力

対象となるディレクトリからファイル名を収集しRUN IDに変換したうえで
RUNに紐づく組成データをBioProjectにネストし出力します。

例 phylum.tsv (値は同じサンプルをidを変えて複製したもの)
```
taxonomy        SRR7723005      SRR7723001
Bacteroidota    81.4176652335257        81.4176652335257
Actinomycetota  9.260924294191692       9.260924294191692
Pseudomonadota  6.472021055729021       6.472021055729021
Bacillota       2.011574111915777       2.011574111915777
Bacillota_C     0.8378153046378185      0.8378153046378185
```

## 環境

Python3.9以上

## 利用方法

- ファイルを指定して変換

```
python kraken2composition.py -i <input dir> -o <output dir>　-e <extension>
```

- -i: inputファイルのディレクトリを指定
- -o: アウトプットファイルのディレクトリを指定
- -e: 読み込む対象となるファイルの拡張子を指定。デフォルトで"csv"が指定されている
