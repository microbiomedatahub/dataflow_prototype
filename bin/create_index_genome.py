import os
import json
import datetime
from xml.etree import ElementTree as ET

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
                
                if display_name in ["pH", "soil pH", "water pH"]:
                    val = ''.join(filter(str.isdigit, value))
                    if val:
                        annotation['sample_ph'].append(float(val))
                elif display_name in ["temperature", "air temperature"]:
                    val = ''.join(filter(str.isdigit, value))
                    if val:
                        annotation['sample_temperature'].append(float(val))

        annotation['sample_ph_range'] = {"min": min(annotation['sample_ph'], default=0), "max": max(annotation['sample_ph'], default=0)}
        annotation['sample_temperature_range'] = {"min": min(annotation['sample_temperature'], default=0), "max": max(annotation['sample_temperature'], default=0)}
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
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
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
            '_annotation': {}
        }
        out.write(json.dumps(annotation) + '\n')


# Usage example:
input_path = "/path/to/input"
output_path = "/path/to/output"

reports = AssemblyReports(input_path, output_path)
reports.parse_summary()
