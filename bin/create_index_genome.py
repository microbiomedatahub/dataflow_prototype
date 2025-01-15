import os
import json
import datetime
import re
from xml.etree import ElementTree as ET

def asm_acc2path(asm_acc):
    parts = asm_acc.replace("GCA_", "GCA").split(".")[0]
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
            'sample_host_disease': [],
            'sample_host_location': [],
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


class AssemblyReports:
    def __init__(self, input_path, output_path, genome_path):
        self.input_path = input_path
        self.output_path = output_path
        self.genome_path = genome_path
        self.source = 'assembly_summary_genbank.txt'

    def parse_summary(self):
        source_file = os.path.join(self.input_path, 'genomes/ASSEMBLY_REPORTS', self.source)
        output_file = os.path.join(self.output_path, f'mdatahub_index_genome-{datetime.date.today()}.jsonl-togo')

        with open(source_file, 'r', encoding='utf-8') as f:
            headers = []
            lines = f.readlines()
            with open(output_file, 'w') as out:
                for i, line in enumerate(lines):
                    if i == 1:
                        headers = line.strip('#').strip().split('\t')
                    elif i > 1:
                        data = dict(zip(headers, line.strip().split('\t')))
                        self.process_row(data, out)

    def process_row(self, row, out):
        if 'derived from metagenome' not in row.get('excluded_from_refseq', ''):
            return

        annotation = {
            'type': 'genome',
            'identifier': row['assembly_accession'],
            'organism': row['organism_name'],
            'description': row['excluded_from_refseq'],
            'data_type': 'Genome sequencing and assembly',
            'organization': row['submitter'],
            'dateCreated': row['seq_rel_date'],
            'properties': row,
            '_annotation': {}
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
                annotation['_annotation']['dfast_stats'] = stats

        # DFASTQC結果から取得
        dfastqc_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'dfastqc', 'dqc_result.json')
        if os.path.exists(dfastqc_path):
            with open(dfastqc_path, 'r') as f:
                dqc_data = json.load(f)
                annotation['_annotation'].update(dqc_data.get('cc_result', {}))

        # 配列ファイルから取得
        genome_fna_path = os.path.join(self.genome_path, asm_acc2path(row['assembly_accession']), row['assembly_accession'], 'genome.fna.gz')
        if os.path.exists(genome_fna_path):
            size = os.path.getsize(genome_fna_path) / (1024 * 1024)
            annotation['_annotation']['data_size'] = f"{size:.2f} MB"

        # 星（quality）計算
        contamination = annotation['_annotation'].get('contamination', 0)
        completeness = annotation['_annotation'].get('completeness', 0)
        sequence_count = int(annotation['_annotation'].get('dfast_stats', {}).get('Number of Sequences', 0))
        rrna_count = int(annotation['_annotation'].get('dfast_stats', {}).get('Number of rRNAs', 0))

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

        out.write(json.dumps(annotation) + '\n')


# Usage example:
input_path = "/work1/mdatahub/app/dataflow_prototype"
output_path = "/work1/mdatahub/app/dataflow_prototype"
genome_path = "/work1/mdatahub/public/genome"

reports = AssemblyReports(input_path, output_path, genome_path)
reports.parse_summary()
