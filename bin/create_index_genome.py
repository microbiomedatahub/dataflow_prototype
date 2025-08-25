import os
import json
import csv
import datetime
import re
import math
import argparse
from xml.etree import ElementTree as ET
import urllib.request
import urllib.parse
from pathlib import Path


def asm_acc2path(asm_acc:str) -> str:
    """
    IDを3文字づつ区切ったファイルが格納されたパスと一致する文字列を生成し返す
    """
    parts = asm_acc.replace("GCA_", "GCA").replace("GCF_", "GCF").split(".")[0]
    return "/".join([parts[i:i+3] for i in range(0, len(parts), 3)])

# deplicated: BioSampleを変換したjsonファイルを取得するため不要
class BioSampleSet:
    def __init__(self, xml_file, params=None):
        self.xml_file = xml_file
        self.params = params if params else {}

    def __iter__(self):
        xml_strs = []
        all_samples = []

        with open(self.xml_file, 'r') as f:
            for line in f:
                xml_strs.append(line.strip())
                if '</BioSample>' in line:
                    docs = "\n".join(xml_strs)
                    samples = ET.fromstring(docs).findall("BioSample")
                    if not samples:
                        raise ValueError("BioSample element not found")
                    all_samples.extend(samples)
                    xml_strs = []

        for sample in all_samples:
            yield BioSample(sample)

    def json_plus_default(self):
        return {
            'sample_count': 0,
            'sample_organism': [],
            'sample_taxid': [],
            'sample_ph': [],
            'sample_temperature': [],
            'sample_host_organism': [],
            'sample_host_organism_id': [],
            'sample_host_disease': [],
            'sample_host_disease_id': [],
            'sample_host_location': [],
            'sample_host_location_id': [],
            'data_size': '0.0 GB'
        }

    def to_json_plus(self):
        annotation = self.json_plus_default()
        for biosample in self:
            annotation['sample_count'] += 1
            annotation['sample_organism'].append(biosample.organism)
            annotation['sample_taxid'].append(biosample.taxid)
            
            for attr in biosample.sample_attributes():
                hname = attr['harmonized_name']
                value = attr['value']
                display_name = attr['display_name']
                
                if display_name in ["pH", "soil pH", "water pH", "fermentation pH" ,"surface moisture pH","wastewater pH"]:
                    val = ''.join(filter(str.isdigit, value))
                    if val:
                        annotation['sample_ph'].append(float(val))
                elif display_name in ["air temperature","annual and seasonal temperature","average temperature","depth (TVDSS) of hydrocarbon resource temperature","dew point","fermentation temperature","food stored by consumer (storage temperature)","host body temperature","hydrocarbon resource original temperature","mean annual temperature","mean seasonal temperature","pour point","sample storage temperature","sample transport temperature","soil temperature","study incubation temperature","surface temperature","temperature","temperature outside house","wastewater temperature"]:
                    val = ''.join(filter(str.isdigit, value))
                    if val:
                        annotation['sample_temperature'].append(float(val))
                elif display_name == "host":
                    annotation['sample_host_organism'].append(value)
                elif display_name in ["disease","fetal health status", "host disease", "health","health status","host health state","host of the symbiotic host disease status","outbreak","study disease"]:
                    annotation['sample_host_disease'].append(value)
                elif re.search("location", display_name, re.IGNORECASE):
                    annotation['sample_host_location'].append(value)


        annotation['sample_ph_range'] = {"min": min(annotation['sample_ph'], default=None), "max": max(annotation['sample_ph'], default=None)}
        annotation['sample_temperature_range'] = {"min": min(annotation['sample_temperature'], default=None), "max": max(annotation['sample_temperature'], default=None)}
        del annotation['sample_ph']
        del annotation['sample_temperature']
        return annotation

# deplicated: BioSampleを変換したjsonファイルを取得するため不要
class BioSample:
    def __init__(self, xml_node):
        self.xml_node = xml_node

    @property
    def organism(self):
        return self.xml_node.find('Description/Organism').attrib.get('taxonomy_name', '')

    @property
    def taxid(self):
        return self.xml_node.find('Description/Organism').attrib.get('taxonomy_id', '')

    @property
    def title(self):
        bs = self.xml_node.find('BioSample')
        try:
            bs_id = bs.attrib['id']
        except:
            bs_id = None
        if bs_id:
            return self.xml_node.find('Description/SampleName').text 

        else:
            return self.xml_node.find('Description/Title').text

    def sample_attributes(self):
        attributes = []
        for attr in self.xml_node.findall('Attributes/Attribute'):
            attributes.append({
                'name': attr.attrib.get('attribute_name', ''),
                'value': attr.text.strip() if attr.text else '',
                'harmonized_name': attr.attrib.get('harmonized_name', ''),
                'display_name': attr.attrib.get('display_name', '')
            })
        return attributes


class Bac2Feature:
    def __init__(self, b2f_path):
        d = {}
        if os.path.exists(b2f_path):
            with open (b2f_path, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    d.update({row['MAG_ID']: row })
        else:
            today = datetime.date.today()
            logs(f"Error processing Bac2Feature: {b2f_path}", f"{today}_bac2feature_error_log.txt") 
        self.b2f_dict = d


    def get_b2f(self,mag_id):
        d = self.b2f_dict.get(mag_id, None)
        if d is None:
            return {}
        else:
            for key, value in d.items():
                try:
                    if value not in ["NA", "NaN"]:
                        num = float(value)
                        rounded_num = round(num, 3)
                        d[key] = rounded_num
                    else:
                        d[key] = None
                except ValueError:
                    d[key] = None
            del d['MAG_ID']
            return d

class GTDB_TK:
    """
    GTDB-TKファイルのパスを指定してGTDB-TKのtaxonomyを取得し、Dictに格納するクラス
    genome_idをキーとして、GTDB-TKのtaxonomyを値とする辞書を生成し、引数として渡されたgenome_idに対応するGTDB-TKのtaxonomyを返す
    """
    def __init__(self, gtdb_tk_path):
        self.gtdb_tk_path = gtdb_tk_path
        self.gtdb_dict = {}
        if os.path.exists(gtdb_tk_path):
            with open(gtdb_tk_path, 'r') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        genome_id = self.extract_genome_id(parts[0])
                        self.gtdb_dict[genome_id] = parts[1]
        else:
            today = datetime.date.today()
            logs(f"Error processing GTDB-TK: {gtdb_tk_path}", f"{today}_gtdbtk_error_log.txt")

    def extract_genome_id(self, path):
        """
        パスからgenome_idを抽出するメソッド
        """
        parts = path.split('/')
        for part in reversed(parts):
            if part.startswith('GCA_') or part.startswith('GCF_'):
                return part
        return None
    
    def get_gtdb_taxonomy(self, genome_id):
        """
        genome_idに対応するGTDB-TKのtaxonomyを返すメソッド
        genome_idが存在しない場合はNoneを返す
        """
        # 文字列では無くリストを返す
        gtdb_taxonomy = self.gtdb_dict.get(genome_id, None)
        if gtdb_taxonomy:
            return gtdb_taxonomy.split(';')
        return []

class BulkInsert:
    def __init__(self, url):
        self.es_url = url
    def insert(self,docs):
        insert_lst = []
        today = datetime.date.today()
        for doc in docs:
            try:
                insert_lst.append({'index': {'_index': 'genome', '_id': doc['identifier']}})
                insert_lst.append(doc)
            except:
                print("cant open doc: ")
        post_data = "\n".join(json.dumps(d) for d in insert_lst) + "\n"
        headers = {"Content-Type": "application/x-ndjson"}
        req = urllib.request.Request(self.es_url, data=post_data.encode('utf-8'),headers=headers)
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            # print(response_data)
            log_str = json.dumps(response_data)
            word = "exception"
            if word in log_str:
                file_name = f"{today}_bulkinsert_error_log.txt"
                logs(log_str, file_name)

class TSV2MEO:
    """
    タブ区切りファイルを { accession: [ {meo_id, meo_label}, ... ] } に変換するクラス
    """
    def __init__(self, tsv_path: str, encoding: str = "cp932"):
        self.tsv_path = Path(tsv_path)
        self.encoding = encoding

    def _make_unique_headers(self, headers):
        """同名カラムが複数ある場合に __1, __2 ... を付けてユニーク化"""
        seen = {}
        unique = []
        for h in headers:
            n = seen.get(h, 0)
            if n == 0:
                unique.append(h)
            else:
                unique.append(f"{h}__{n}")
            seen[h] = n + 1
        return unique

    def _first_header_startswith(self, headers, prefix):
        """ヘッダの中から指定 prefix で始まる最初のカラム名を返す"""
        for h in headers:
            if h.startswith(prefix):
                return h
        return None

    def _normalize(self, s):
        """空や NA を無効化"""
        if s is None:
            return ""
        s = str(s).strip()
        if s == "" or s.upper() == "NA":
            return ""
        return s

    def parse(self) -> dict:
        """
        TSV ファイルを読み込み、辞書を返す
        { accession: [ {meo_id, meo_label}, ... ] }
        """
        with self.tsv_path.open("r", newline="", encoding=self.encoding) as f:
            raw_reader = csv.reader(f, delimiter="\t")
            try:
                raw_headers = next(raw_reader)
            except StopIteration:
                raise ValueError("空ファイルです")

            headers = self._make_unique_headers(raw_headers)
            accession_col = self._first_header_startswith(headers, "Assembly Accession")
            if not accession_col:
                raise ValueError('"Assembly Accession" 列が見つかりません')

            # MEO 系のカラムを探索
            meo_id_cols    = [h for h in headers if h.startswith("MEOID")] or [h for h in headers if h.startswith("MOID")]
            meo_label_cols = [h for h in headers if h.startswith("MEOlabel")]
            meo_pairs = []
            max_len = max(len(meo_id_cols), len(meo_label_cols)) if (meo_id_cols or meo_label_cols) else 0
            for k in range(max_len):
                id_col    = meo_id_cols[k]    if k < len(meo_id_cols)    else None
                label_col = meo_label_cols[k] if k < len(meo_label_cols) else None
                meo_pairs.append((id_col, label_col))

            # DictReader で再度読み込み
            f.seek(0)
            dict_reader = csv.DictReader(f, fieldnames=headers, delimiter="\t")
            next(dict_reader)  # ヘッダをスキップ

            out = {}
            gc_regex = re.compile(r"^(GCA|GCF)_\d+\.\d+$")

            for row in dict_reader:
                acc = self._normalize(row.get(accession_col))
                if not acc:
                    continue

                # 複数の "Assembly Accession" がある場合に GCA/GCF 形式なら優先
                alt_acc_cols = [h for h in headers if h != accession_col and h.startswith("Assembly Accession")]
                for h in alt_acc_cols:
                    cand = self._normalize(row.get(h))
                    if cand and gc_regex.match(cand):
                        acc = cand
                        break

                meo_list = []
                for (id_col, label_col) in meo_pairs:
                    meo_id    = self._normalize(row.get(id_col))    if id_col    else ""
                    meo_label = self._normalize(row.get(label_col)) if label_col else ""
                    if meo_id or meo_label:
                        entry = {}
                        if meo_id:    entry["id"] = meo_id
                        if meo_label: entry["label"] = meo_label
                        meo_list.append(entry)

                out.setdefault(acc, []).extend(meo_list)

        return out


def logs(message: str, file_name: str):
    with open(f"bin/logs/{file_name}", "a") as f:
        f.write(message  + "\n")


class AssemblyReports:
    def __init__(self, summary_path, genome_path, bulk_api, dtype, b2f_path, gtdb_tk_path):
        self.summary_path = summary_path
        self.genome_path = genome_path
        # data_typeはMAGまたはGが指定される。flagとして使用する.
        self.dtype = dtype
        # TODO: b2fファイルが存在しない場合空のobjを返す仕様を検討
        self.b2f = Bac2Feature(b2f_path)
        # dtypeがMAGの場合MEO辞書を読み込む。
        self.meo = TSV2MEO(MEO_TSV_PATH) if dtype == "MAG" else None
        # GTDB-TKのパスを指定してGTDB-TKのtaxonomyを取得する
        self.gtdb_tk = GTDB_TK(gtdb_tk_path)
        self.bulkinsert = BulkInsert(bulk_api)
        self.batch_size = 1000
        self.cnt = 0

    def parse_summary(self):
        # DEP.：output_file出力しないため不要
        # output_file = os.path.join("/work1/mdatahub/private/genomes/",f'mdatahub_index_genome-{datetime.date.today()}.jsonl')
        try:
            with open(self.summary_path, 'r', encoding='utf-8') as f:
                headers = []
                lines = f.readlines()
                l = 0
                docs = []
                for i, line in enumerate(lines):
                    if i == 1:
                        headers = line.strip('#').strip().split('\t')
                    elif i > 1:
                        data = dict(zip(headers, line.strip().split('\t')))
                        doc = self.process_row(data)
                        if doc:
                            docs.append(doc)
                            l += 1
                            self.cnt += 1
                            if l > self.batch_size:
                                self.bulkinsert.insert(docs)
                                docs = []
                                l = 0
                if len(docs) > 0:
                    self.bulkinsert.insert(docs)
                print(f"{self.cnt} records processed.")
        except Exception as e:
            print(f"Error processing assembly summary: {self.summary_path}")
            print(f"Exception: {e}")
                    
    def process_row(self, row):
        # TODO: self.dtypeとしてdata_typeは指定されるためdata_typeの初期化は不要。dtypeで条件式を書き換える。
        today = datetime.date.today()
        # row['assembly_accession'] のプレフィックスがGCAの場合
        # if row['assembly_accession'].startswith('GCA'):
        if self.dtype == "MAG":
            data_type = "MAG"
            data_source = "INSDC"
            if 'derived from metagenome' not in row.get('excluded_from_refseq', ''):
                return
        # row['assembly_accession'] のプレフィックスがGCFの場合       
        # elif row['assembly_accession'].startswith('GCF'):
        elif self.dtype == "G":
            data_type = "G"
            data_source = "RefSeq"
            if not row['relation_to_type_material'].startswith("assembly"):
                return
        else:
            # TODO: MGnify対応
            data_type = ""
            data_source = ""
            return

        genome_dir = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'])
        if not os.path.exists(genome_dir):
            #print(f"Directory does not exist: {genome_dir}")
            return

        # dateのフォーマットをgenbankのフォーマットに変換
        row['seq_rel_date'] = row['seq_rel_date'].replace("-", "/") 

        # TODO: annotationという変数名が内包する属性と同一で誤解の原因となるため、別の名前に変更するex.metadata
        annotation = {
            'type': 'genome',
            'identifier': row['assembly_accession'],
            'organism': row['organism_name'],
            'title': row['organism_name'],
            'description': row['excluded_from_refseq'],
            'data type': 'Genome sequencing and assembly',
            'organization': row.get('submitter', row.get('asm_submitter')),
            'publication': [ { } ],
            'properties': row,
            'dbXrefs': [],
            'distribution': None,
            'Download': None,
            'status': 'public',
            'visibility': None,
            'dateCreated': row['seq_rel_date'].replace("/", "-"),
            'dateModified': row['seq_rel_date'].replace("/", "-"),
            'datePublished': row['seq_rel_date'].replace("/", "-"),
            '_annotation': {},
            'data_type': data_type,
            'data_source': data_source
        }

        biosample_plus_default = {
            'sample_count': 0,
            'sample_organism': [],
            'sample_taxid': [],
            'sample_ph': [],
            'sample_temperature': [],
            'sample_host_organism': [],
            'sample_host_organism_id': [],
            'sample_host_disease': [],
            'sample_host_disease_id': [],
            'sample_host_location': [],
            'sample_host_location_id': [],
            'data_size': '0.0 GB'
        }

        # BioSamplelSetのxmlではなくgenomeディレクトリに配置されたjsonを読み込むように変更する
        bs_json_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], f"{row['biosample']}.json") 
        try:
            if os.path.exists(bs_json_path):
                with open(bs_json_path, 'r') as f:
                    annotation['_annotation'] = json.load(f)
            else:
                annotation['_annotation'] = biosample_plus_default
        except Exception as e:
            logs(f"No biosample.json file: {dfast_stats_path}", f"{today}_bsjson_error_log.txt")


        # DEP.: BioSampleを変換したjsonファイルを取得するため不要
        """
        sample_xml_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], f"{row['biosample']}.xml")
        try:
            if os.path.exists(sample_xml_path):
                biosample_set = BioSampleSet(sample_xml_path)
                annotation['_annotation'] = biosample_set.to_json_plus()
            else:
                annotation['_annotation'] = BioSampleSet('').json_plus_default()
        except Exception as e:
            print(f"Error processing BioSample XML: {sample_xml_path}")
            print(f"Exception: {e}")
        """

        # DFAST結果から取得
        dfast_stats_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'dfast', 'statistics.txt')
        if os.path.exists(dfast_stats_path):
            with open(dfast_stats_path, 'r') as f:
                stats = {line.split('\t')[0]: line.split('\t')[1].strip() for line in f}
                annotation['_dfast'] = stats
        else:
            annotation['_dfast'] = {}
            logs(f"Error processing DFAST statistics: {dfast_stats_path}", f"{today}_dfast_error_log.txt")

        # DFASTQC結果から取得
        dfastqc_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'dfastqc', 'dqc_result.json')
        if os.path.exists(dfastqc_path):
            with open(dfastqc_path, 'r') as f:
                dqc_data = json.load(f)
                annotation['has_analysis'] = True
                annotation['_dfastqc'] = dqc_data
                annotation['_annotation'].update(dqc_data.get('cc_result', {}))

                # data_typeがGの場合（単離菌ゲノムの場合）DFASTQCから"_gtdb_taxon"を取り出し_gtdb_taxonとして追加
                if self.dtype == "G":
                    gtdb_result = dqc_data.get('gtdb_result')
                    if gtdb_result:
                        if isinstance(gtdb_result, list):
                            gtdb_result = gtdb_result[0]

                        if isinstance(gtdb_result, dict):
                            gtdb_species = gtdb_result.get('gtdb_species')
                            ani = gtdb_result.get('ani')
                            gtdb_taxon = gtdb_result.get('gtdb_taxonomy')
                            if gtdb_taxon is None:
                                gtdb_taxon_list = gtdb_taxon.split(";")
                                if ani > 95:
                                    gtdb_taxon_list.append(gtdb_species)
                                annotation['_gtdb_taxon'] = gtdb_taxon_list

        else:
            annotation['has_analysis'] = False
            annotation['_dfastqc'] = {}
            # TODO: dfastqcがない場合completeness=0をdefault値として入力するという処理が正しいか確認
            annotation['_annotation']['completeness'] = 0
            logs(f"Error processing DFASTQC: {dfastqc_path}", f"{today}_dfastqc_error_log.txt")

        # 配列ファイルから取得
        genome_fna_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'genome.fna.gz')
        if os.path.exists(genome_fna_path):
            size = os.path.getsize(genome_fna_path) / (1024 * 1024)
            annotation['_annotation']['data_size'] = f"{size:.3f} MB"

        genome_count = 1
        annotation['_annotation']['genome_count'] = genome_count

        # Bac2Featureから取得
        annotation['_bac2feature'] = self.b2f.get_b2f(row['assembly_accession'])

        # TODO: GTDB-TKのパーサークラスを追加して_gtdb_taxonの取得を行う
        # _gtdb_taxonを取得
        # TODO: data_typeがMAGの場合のみ_gtdb_taxonを取得するように変更
        if self.dtype == "MAG":
            annotation['_gtdb_taxon'] = self.gtdb_tk.get_gtdb_taxonomy(row['assembly_accession'])

        # DEB.: GTDB taxonomyの情報はGTDB-TKの出力ファイルから取得するように変更したため不要
        """
        
        # _dfastqc.gtdb_resultがlistとして存在する場合、最初の要素からgtdb_taxonomyを取得する
        if type(annotation['_dfastqc'].get('gtdb_result')) is list and len(annotation['_dfastqc'].get('gtdb_result')) > 0:
            try:
                gtdb_result = annotation['_dfastqc'].get('gtdb_result', [])[0]
                gtdb_taxonomy = gtdb_result.get('gtdb_taxonomy')
                if gtdb_taxonomy:
                    annotation['_gtdb_taxon'] = gtdb_taxonomy.split(";")
                gtdb_species = gtdb_result.get('gtdb_species')
                if gtdb_species:
                    annotation['_gtdb_taxon'].append(gtdb_species)
            except:
                print(f"Error processing GTDB taxonomy: {row['assembly_accession']}")
                annotation['_gtdb_taxon'] = []
        else:
            annotation['_gtdb_taxon'] = []
        """

        # _genome_taxonにtaxonomy検索用の文字列をキーワードとして追加
        annotation['_genome_taxon'] = annotation['organism'].split(" ")
        # _gtdb_taxonのlen()が評価されるので_gtdb_taxonはlistである必要がある
        if len(annotation.get('_gtdb_taxon', [])) > 0:
            # _gtdb_taxonが存在する場合、_genome_taxonに追加
            annotation['_genome_taxon'].extend(annotation['_gtdb_taxon'])
            # _gtdb_taxonのprefix（*__）を削除し、さらに空白と_で分割した文字列を配列に追加
            for gtdb_taxon in annotation['_gtdb_taxon']:
                if len(gtdb_taxon) > 3 and gtdb_taxon[1:3] == "__":
                    gtdb_taxon = gtdb_taxon[3:]
                annotation['_genome_taxon'].extend(gtdb_taxon.replace("_", " ").split(" "))
        
        # _meoにMEOのIDとラベルを配列で追加
        if self.meo:
            meo_data = self.meo.get_meo_data(row['assembly_accession'])
            if meo_data:
                annotation['_meo'] = meo_data

        # 星（quality）計算
        contamination = annotation['_annotation'].get('contamination', -1)
        completeness = annotation['_annotation'].get('completeness', 0)
        sequence_count = int(annotation.get('_dfast', {}).get('Number of Sequences', 0))
        rrna_count = int(annotation.get('_dfast', {}).get('Number of rRNAs', 0))

        if annotation['has_analysis']:
            star = 1
            if contamination < 10:
                star += 1
            if completeness > 60:
                star += 1
            if 0 < sequence_count < 30:
                star += 1
            if rrna_count > 2:
                star += 1
        else:
            star = 0

        annotation['quality'] = star
        annotation['quality_label'] = '⭐️' * star


        # genome.json出力
        genome_json_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'genome.json')
        with open(genome_json_path, 'w') as genome_file:
            json.dump(annotation, genome_file, indent=4)

        # print(json.dumps(annotation, indent=4))
        # print(row['assembly_accession'])
        # DEP.: ESに直接insertするのでjsonlを作らない
        # out.write(json.dumps(annotation) + '\n')
        return annotation

if __name__ == "__main__":
    # bac2featureのパス.単一のファイルしかない場合は以下に指定する
    # B2F = "/work1/mdatahub/private/insdc/b2f/20241221_All_predicted_traits.txt"
    ASSEMBLY_SUMMARY_GENBANK = "/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt"
    ASSEMBLY_SUMMARY_REFSEQ = "/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt"
    GTDB_TK_PATH = "/work1/mdatahub/private/genomes/GTDB/GTDB_tk_2025_7.txt"
    MEO_TSV_PATH = "/work1/mdatahub/private/genomes/MEO/20250816_MDatahub_MAG_MAGInfo18.txt"
    parser = argparse.ArgumentParser(description="Process genome assembly reports.")
    parser.add_argument("-i", "--insdc_path", type=str, default=ASSEMBLY_SUMMARY_GENBANK, help="Path to the summary file.")
    parser.add_argument("-r", "--refseq_path", type=str, default=ASSEMBLY_SUMMARY_REFSEQ, help="Path to the summary file.")
    parser.add_argument("-g", "--genome_path", type=str, default="/work1/mdatahub/public/genome", help="Path to the genome root directory.")
    parser.add_argument("-e", "--es_bulk_api", type=str, default="http://localhost:9201/_bulk", help="Elasticsearch bulk API endpoint.")
    args = parser.parse_args()

    for summary_path in [args.insdc_path, args.refseq_path]:
        # Bac2Featureのファイルがtypeごと存在する場合以下にパスを指定する
        if summary_path == args.insdc_path:
            data_type = "MAG"
            # MAGのBac2Featureを指定
            B2F = "/work1/mdatahub/private/insdc/b2f/assembly_summary_genbank.txt.mag.needs.bac2f.txt"
        elif summary_path == args.refseq_path:
            data_type = "G"
            # RefSeq-単離菌のBac2Featureを指定
            B2F = "/work1/mdatahub/private/refseq/b2f/id_organism_with_phenotype3.tsv"
        reports = AssemblyReports(summary_path, args.genome_path, args.es_bulk_api, data_type, B2F, GTDB_TK_PATH, MEO_TSV_PATH)
        reports.parse_summary()
