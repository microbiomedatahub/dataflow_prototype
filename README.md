# データの新規作成・更新手順

データや解析データの取得およびMdatahub環境へのデータ配置、オントロジーマッピングなどアノテーションおよびデータ形式変換、検索データのElasticsearchデータ投入について記載する

## セットアップ 
```
git clone git@github.com:microbiomedatahub/dataflow_prototype.git
cd dataflow_prototype
```


## 新規作成
### 1. 最新のbioproject.xml取得
```/work1/mdatahub/repos/dataflow_prototype/bioproject.xml```
のシンボリックリンクのsourceが最新データ

```
[mdb_dev@cs9 dataflow_prototype]$ pwd
/work1/mdatahub/repos/dataflow_prototype
[mdb_dev@cs9 dataflow_prototype]$ ls -la bioproject.xml
lrwxrwxrwx. 1 mdb_dev mdb_dev 23  6月 12  2023 bioproject.xml -> bioproject-20230612.xml
```

### 2. 対象となるProjectサブセットのIDリストを取得
* mag-insdc
`create_project_accessions.rb `

* gnm-refseq
PGAPを使ってないいにしえのモデル微生物３件。全てのリファレンスゲノムは、強制的に、PRJNA224116のRefSeqエントリーに紐づけることにする
```
[tf@at044 ~]$ grep "assembly from type material" /lustre9/open/shared_data/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt |egrep "archaea|bacteria" |cut -f2 |sort |uniq -c
   21745 PRJNA224116
      1 PRJNA57675
      1 PRJNA57777
      1 PRJNA57799
```

* mag-mgnify
```
TODO
```

* test
```
TODO
```

### 3. プロジェクト毎に各種データを取得
`bioproject_mget.rb`

### 4.Elasticsearch bulk APIで投入用のLine-delimited JSON形式ファイルを生成

`create_indexes.rb`

### 5. Elasticsearchへの全長jsonlのbulk import
Elasticsearchは100MBを超えるJSONファイルのbulk importができないため、このサイズを超えるデータは分割してインポートします。

```
mkdir bulk_import
bash bin/split.sh #TODO:対象ファイルと出力先の修正
curl -XDELETE http://localhost:9200/bioproject 
bash bin/bulk_import.sh
```

---
- テストデータを利用した動作確認が可能です。
```
ruby bin/create_indexes.rb testdata
```

- 以下は、レポジトリにある取得済の入力データおよび出力データです。
```
testdata/
├── bioproject.xml               ## 入力データ
├── bioproject.json              ## 中間ファイル
├── mdatahub_index_project.jsonl ## 生成インデックスデータ
└── project
    ├── PRJDB
    │   ├── 004
    │   │   ├── PRJDB004176
    │   │   │   ├── PRJDB4176-biosampleset.xml ##入力データ
    │   │   │   ├── PRJDB4176.dblink
    │   │   │   └── PRJDB4176.xml
    │   │   └── PRJDB004224
    │   │       ├── PRJDB4224-biosampleset.xml ##入力データ
    │   │       ├── PRJDB4224.dblink
    │   │       └── PRJDB4224.xml
```



## Data model

### project
```
{
  "type": "bioproject",
  "identifier": "PRJNA189273",
  "organism": "freshwater metagenome",
  "title": "Mississippi River Targeted Locus (Loci)",
  "description": "Raw sequence reads of the V6 hypervariable region of 16S rDNA from microbial communities within the Mississippi River.",
  "data type": "targeted loci",
  "organization": "University of Minnesota",
  "publication": [
    {
      "id": "25339945",
      "Title": "Bacterial community structure is indicative of chemical inputs in the Upper Mississippi River."
    }
  ],
  "properties": null,
  "dbXrefs": [],
  "distribution": null,
  "Download": null,
  "status": "public",
  "visibility": null,
  "dateCreated": "2013-02-12",
  "dateModified": "2013-02-12",
  "_annotation": {
    "sample_count": 147,
    "sample_organism": [
      "freshwater metagenome"
    ],
    "sample_taxid": [
      "449393"
    ],
    "sample_host_organism": [],
    "sample_host_organism_id": [],
    "sample_host_disease": [],
    "sample_host_disease_id": [],
    "sample_host_location": [
      "USA: Minnesota",
      "USA: Mississippi River",
      "USA: MN, Mississippi River",
      "Mississippi River"
    ],
    "sample_host_location_id": [],
    "data_size": "0.0 GB",
    "sample_ph_range": {
      "min": 6.89,
      "max": 9.1
    },
    "sample_temperature_range": {
      "min": 3.6,
      "max": 27
    },
    "genome_count": 0
  },
  "has_analysis": false
}
```

### genome
```
{
  "type": "genome",
  "identifier": "PRJDB11811_OceanDNA-a1015",
  "organism": "hogehoge",
  "title": "",
  "description": "",
  "data type": "Genome sequencing and assembly",
  "organization": "Atmosphere and Ocean Research Institute, The University of Tokyo; 5-1-5 Kashiwanoha, Kashiwa, Chiba 277-8564, Japan",
  "publication": [
    {
      "id": "35715423",
      "Title": "The OceanDNA MAG catalog contains over 50,000 prokaryotic genomes originated from various marine environments."
    }
  ],
  "properties": null,
  "dbXrefs": [],
  "distribution": null,
  "Download": null,
  "status": "public",
  "visibility": null,
  "dateCreated": "2023-04-19",
  "dateModified": "2023-04-19",
  "datePublished": "2022-04-07T14:46:34Z",
  "_annotation": {
    "sample_count": 1,
    "sample_organism": [],
    "sample_taxid": [],
    "sample_host_organism": [],
    "sample_host_organism_id": [],
    "sample_host_disease": [],
    "sample_host_disease_id": [],
    "sample_host_location": [],
    "sample_host_location_id": [],
    "data_size": "0.0 GB",
    "sample_ph_range": {
      "min": null,
      "max": null
    },
    "sample_temperature_range": {
      "min": null,
      "max": null
    },
    "completeness": 91.67,
    "contamination": 0,
    "strain_heterogeneity": 0
  },
  "data_type": "low-quality MAG",
  "data_source": "INSDC"
}
```
