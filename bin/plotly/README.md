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

```
$ python kraken2plotlyjson.py -i <入力するファイルを配置したディレクトリのパス> [-o 出力するディレクトリのパス]

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