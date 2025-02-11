import os
import urllib.request
import subprocess
import json
import base64
import time
import gzip
import shutil
import re
from xml.etree import ElementTree as ET
from typing import Any, Dict, Optional

# from dotenv import load_dotenv

# Load environment variables from .env file
# load_dotenv()

def asm_acc2path(asm_acc, dataset):
    if dataset == "insdc":
        parts = asm_acc.replace("GCA_", "GCA").split(".")[0]
    else:
        parts = asm_acc.replace("GCF_", "GCF").split(".")[0]
    return "/".join([parts[i:i+3] for i in range(0, len(parts), 3)])

def create_genome_directory(genome_id):

    os.environ['MDATAHUB_PATH_GENOME'] = '/work1/mdatahub/public/genome'
    # for debug
    #os.environ['MDATAHUB_PATH_GENOME'] = '/tmp/mdatahub/public/genome'
    base_path = os.getenv('MDATAHUB_PATH_GENOME')
    if not (genome_id.startswith("GCF_") or genome_id.startswith("GCA_")) or len(genome_id.split(".")) != 2:
        raise ValueError("Invalid genome ID format. Expected format: 'GCF_XXXXXXXXX.X'")
    relative_path = asm_acc2path(genome_id, dataset)
    dir_path = os.path.join(base_path, relative_path, genome_id)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Directory created: {dir_path}")
    return dir_path

def download_genomic_file(genome_id, genome_url):
    original_file_name = genome_url.rstrip("/").split("/")[-1] + "_genomic.fna.gz"
    compressed_file_name = "genome.fna.gz"
    uncompressed_file_name = "genome.fna"
    print(f"Downloading file for genome_id: {genome_id}")
    target_dir = create_genome_directory(genome_id)
    compressed_path = os.path.join(target_dir, compressed_file_name)
    uncompressed_path = os.path.join(target_dir, uncompressed_file_name)
    file_url = genome_url.rstrip("/") + "/" + original_file_name

    # Download the file if not exists
    if not os.path.exists(compressed_path):
        try:
            print(f"Downloading {file_url} to {compressed_path}...")
            urllib.request.urlretrieve(file_url, compressed_path)
            print(f"Download completed and saved as {compressed_path}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} while downloading {file_url}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} while accessing {file_url}")

    # Uncompress the file if not exists
    if not os.path.exists(uncompressed_path):
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(uncompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"File decompressed to {uncompressed_path}")
        except Exception as e:
            print(f"Failed to decompress {compressed_path}: {e}")

    return f"https://mdatahub.org/public/genome/{asm_acc2path(genome_id, dataset)}/{genome_id}/genome.fna"

def fetch_biosample_metadata(biosample_id, genome_id):
    target_dir = create_genome_directory(genome_id)
    xml_file_path = os.path.join(target_dir, f"{biosample_id}.xml")
    json_file_path = os.path.join(target_dir, f"{biosample_id}.json")
    if not os.path.exists(xml_file_path):
        print(f"Fetching metadata for {biosample_id}...")
        command = ["efetch", "-db", "biosample", "-id", biosample_id, "-mode", "xml"]
        with open(xml_file_path, "w") as xml_file:
            subprocess.run(command, stdout=xml_file, check=True)
        print(f"Metadata fetched and saved to {xml_file_path}")

        biosample_set = BioSampleSet(xml_file_path)
        biosample_data = biosample_set.to_json_plus()
    else:
        #xml fileがあって、jsonがない場合
        if os.path.exists(xml_file_path):
            biosample_set = BioSampleSet(xml_file_path)
            biosample_data = biosample_set.to_json_plus()
        else:
            biosample_data = BioSampleSet('').json_plus_default()

    with open(json_file_path, "w") as json_file:
        json.dump(biosample_data, json_file, indent=4)

    print(f"Metadata saved to {json_file_path}")

# from create_index_genome.py
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

# from create_index_genome.py
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

def execute_dfast(query_file, genome_id):
    USERNAME = os.getenv("DFAST_USERNAME", "dfast-dev-user")
    PASSWORD = os.getenv("DFAST_PASSWORD", "dfast-dev-password")
    BASE_WF_PARAMS = {
        "query_file": query_file,
        "perform_taxonomy_check": False,
        "perform_completeness_check": False,
        "perform_gtdb_taxonomy_assignment": False,
        "title": genome_id,
        "organism": "",
        "locus_tag_prefix": "LOCUS",
        "minimum_length": 200,
        "genetic_code": 11,
        "sort_sequence": False,
        "fix_origin": False,
        "offset": 100,
        "cds_prediction": "metagene_annotator",
        "rrna_prediction": "barrnap",
        "trna_prediction": "aragorn",
        "crispr_prediction": "crt",
        "evalue": "1e-6",
        "pident": 0,
        "q_cov": 75,
        "s_cov": 75,
        "additional_database": "disable",
        "additional_evalue": "1e-6",
        "additional_pident": 0,
        "additional_q_cov": 75,
        "additional_s_cov": 75,
        "enable_hmm": False,
        "enable_cdd": False,
        "enable_amr": False
    }
    DFAST_API_URL = "https://dfast-dev.ddbj.nig.ac.jp/api"
    def get_access_token():
        token_url = "https://accounts-staging.ddbj.nig.ac.jp/realms/master/protocol/openid-connect/token"
        data = {
            "client_id": "dfast-dev",
            "username": USERNAME,
            "password": PASSWORD,
            "grant_type": "password"
        }
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            return response["access_token"]
    ACCESS_TOKEN = get_access_token()
    req = urllib.request.Request(
        f"{DFAST_API_URL}/workflows/dfc/runs",
        data=json.dumps(BASE_WF_PARAMS).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode("utf-8"))
            run_id = response_data["run_id"]
            print(f"Creating DFAST job for genome_id: {genome_id}")
            print(f"DFAST job submitted. Run ID: {run_id}")
            return run_id
    except Exception as e:
        print(f"Failed to submit a DFAST job for {query_file}: {e}")
        return None

def process_assembly_summary(file_path, dataset):
    with open(file_path, 'r') as file:
        count = 0
        for line in file:
            if line.startswith("#"):
                continue
            columns = line.strip().split("\t")
            genome_id = columns[0]
            biosample_id = columns[2]
            genome_url = columns[19]
            relation_to_type_material = columns[21] if len(columns) > 21 else ""

            #if count >= 10 :
            #    break
            #if not genome_id == 'GCF_004341395.1':
            #    continue
            if columns[2] == "":
                continue
            if (dataset == "insdc" and "derived from metagenome" in columns[20]) or (dataset == "refseq" and relation_to_type_material.startswith("assembly")):
                genomic_file_url = download_genomic_file(genome_id, genome_url)
                fetch_biosample_metadata(biosample_id, genome_id)
                #execute_dfast(genomic_file_url, genome_id)
                count += 1

# Example usage
# wget -O assembly_summary_refseq-20250116.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt
# ln -s assembly_summary_refseq-20250116.txt assembly_summary_refseq.txt

import sys

dataset = sys.argv[1] if len(sys.argv) > 1 else "refseq"
if dataset == "insdc":
    assembly_summary_path = "/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt"
    #assembly_summary_path = "/Users/tf/github/dataflow_prototype/genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt"
else:
    assembly_summary_path = "/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt"
    #assembly_summary_path = "/Users/tf/github/dataflow_prototype/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt"

process_assembly_summary(assembly_summary_path, dataset)