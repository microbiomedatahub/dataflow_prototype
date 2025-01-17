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


def asm_acc2path(asm_acc):
    parts = asm_acc.replace("GCA_", "GCA").replace("GCF_", "GCF").split(".")[0]
    return "/".join([parts[i:i+3] for i in range(0, len(parts), 3)])

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
        with open (b2f_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                d.update({row['MAG_ID']: row })
        self.b2f_dict = d

    def get_b2f(self,mag_id):
        d = self.b2f_dict.get(mag_id)
        for key, value in d.items():
            try:
                if isinstance(value, (int, float)):
                    num = float(value)
                    rounded_num = round(num, 3)
                    d[key] = rounded_num
                else:
                    d[key] = None
            except ValueError:
                d[key] = None
        return d


class BulkInsert:
    def __init__(self, url):
        self.es_url = url
    def insert(self,docs):
        insert_lst = []
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
            # TODO: エラーを検出しlogファイルに残す処理があると良い
            log_str = json.dumps(response_data)
            word = "exception"
            if word in log_str:
                logs(log_str)


def logs(message: str):
    #dir_name = os.path.dirname(args.output)
    log_file = "bulkinsert_error_log.txt"
    with open(log_file, "a") as f:
        f.write(message  + "\n")


class AssemblyReports:
    def __init__(self, summary_path, genome_path, bulk_api):
        self.summary_path = summary_path
        self.genome_path = genome_path
        self.b2f = Bac2Feature('/work1/mdatahub/public/dev/20241221_All_predicted_traits.txt')
        # TODO: urlはコマンド引数もしくは環境変数にする
        self.bulkinsert = BulkInsert(bulk_api)
        self.batch_size = 1000


    def parse_summary(self):
        #TODO：output_file出力してない
        output_file = os.path.join("/work1/mdatahub/private/genomes/",f'mdatahub_index_genome-{datetime.date.today()}.jsonl')
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
                        if l > self.batch_size:
                            self.bulkinsert.insert(docs)
                            docs = []
                            l = 0
            if len(docs) > 0:
                self.bulkinsert.insert(docs)

                    

    #def process_row(self, row, out):
    def process_row(self, row):
        # row['assembly_accession'] のプレフィックスがGCAの場合
        if row['assembly_accession'].startswith('GCA'):
            if 'derived from metagenome' not in row.get('excluded_from_refseq', ''):
                return
        # row['assembly_accession'] のプレフィックスがGCFの場合                
        elif row['assembly_accession'].startswith('GCF'):
            if not row['relation_to_type_material'].startswith("assembly"):
                return
        else:
        # TODO: MGnify対応
            return

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
            'data_type': 'MAG',
            'data_source': 'INSDC' 
        }

        # BioSample.xmlからメタデータ取得
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

        # DFAST結果から取得
        dfast_stats_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'dfast', 'statistics.txt')
        if os.path.exists(dfast_stats_path):
            with open(dfast_stats_path, 'r') as f:
                stats = {line.split('\t')[0]: line.split('\t')[1].strip() for line in f}
                annotation['_dfast'] = stats

        # DFASTQC結果から取得
        dfastqc_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'dfastqc', 'dqc_result.json')
        if os.path.exists(dfastqc_path):
            with open(dfastqc_path, 'r') as f:
                dqc_data = json.load(f)
                annotation['has_analysis'] = True
                annotation['_dfastqc'] = dqc_data
                annotation['_annotation'].update(dqc_data.get('cc_result', {}))
        else:
            annotation['has_analysis'] = False
            annotation['_dfastqc'] = {}

        # 配列ファイルから取得
        genome_fna_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'genome.fna.gz')
        if os.path.exists(genome_fna_path):
            size = os.path.getsize(genome_fna_path) / (1024 * 1024)
            annotation['_annotation']['data_size'] = f"{size:.3f} MB"

        genome_count = 1
        annotation['_annotation']['genome_count'] = genome_count


        # Bac2Featureから取得
        annotation['_bac2feature'] = self.b2f.get_b2f(row['assembly_accession'])
        del annotation['_bac2feature']['MAG_ID']

        # 星（quality）計算
        contamination = annotation['_annotation'].get('contamination', 0)
        completeness = annotation['_annotation'].get('completeness', 0)
        sequence_count = int(annotation['_annotation'].get('_dfast', {}).get('Number of Sequences', 0))
        rrna_count = int(annotation['_annotation'].get('_dfast', {}).get('Number of rRNAs', 0))

        star = 1
        if contamination < 10:
            star += 1
        if completeness > 60:
            star += 1
        if sequence_count < 30:
            star += 1
        if rrna_count > 2:
            star += 1

        annotation['quality'] = star
        annotation['quality_label'] = '⭐️' * star


        # genome.json出力
        genome_json_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'genome.json')
        #FIXME
        #with open(genome_json_path, 'w') as genome_file:
        #    json.dump(annotation, genome_file, indent=4)

        # deprecated
        # ESに直接insertするのでjsonlを作らない
        # out.write(json.dumps(annotation) + '\n')
        return annotation

# Usage example:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process genome assembly reports.")
    parser.add_argument("-s", "--summary_path", type=str, default="/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt", help="Path to the summary file.")
    parser.add_argument("-g", "--genome_path", type=str, default="/work1/mdatahub/public/genome", help="Path to the genome directory.")
    parser.add_argument("-e", "--es_bulk_api", type=str, default="http://localhost:9201/_bulk", help="Elasticsearch bulk API endpoint.")

    args = parser.parse_args()

    reports = AssemblyReports(args.summary_path, args.genome_path, args.es_bulk_api)
    reports.parse_summary()
