import os
import urllib.request
import subprocess
import json
import base64
import time
from typing import Any, Dict, Optional
#from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv()

def asm_acc2path(asm_acc):
    parts = asm_acc.replace("GCF_", "GCF").split(".")[0]
    return "/".join([parts[i:i+3] for i in range(0, len(parts), 3)])

def create_genome_directory(genome_id):
    #print(f"Creating directory for genome_id: {genome_id}")
    os.environ['MDATAHUB_PATH_GENOME'] = '/work1/mdatahub/public/genome'
    base_path = os.getenv('MDATAHUB_PATH_GENOME')
    if not genome_id.startswith("GCF_") or len(genome_id.split(".")) != 2:
        raise ValueError("Invalid genome ID format. Expected format: 'GCF_XXXXXXXXX.X'")
    relative_path = asm_acc2path(genome_id)
    dir_path = os.path.join(base_path, relative_path, genome_id)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Directory created: {dir_path}")
    return dir_path

def download_genomic_file(genome_id, genome_url):
    original_file_name = genome_url.rstrip("/").split("/")[-1] + "_genomic.fna.gz"
    renamed_file_name = "genome.fna.gz"
    print(f"Downloading file for genome_id: {genome_id}")
    target_dir = create_genome_directory(genome_id)
    download_path = os.path.join(target_dir, renamed_file_name)
    file_url = genome_url.rstrip("/") + "/" + original_file_name
    if not os.path.exists(download_path):
        try:
            print(f"Downloading {file_url} to {download_path}...")
            urllib.request.urlretrieve(file_url, download_path)
            print(f"Download completed and saved as {download_path}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} while downloading {file_url}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} while accessing {file_url}")
    return f"https://mdatahub.org/public/genome/{asm_acc2path(genome_id)}/{genome_id}/genome.fna.gz"

def fetch_biosample_metadata(biosample_id, genome_id):
    #print(f"Fetching metadata for genome_id: {genome_id}")
    target_dir = create_genome_directory(genome_id)
    xml_file_path = os.path.join(target_dir, f"{biosample_id}.xml")
    if not os.path.exists(xml_file_path):
        print(f"Fetching metadata for {biosample_id}...")
        command = ["efetch", "-db", "biosample", "-id", biosample_id, "-mode", "xml"]
        with open(xml_file_path, "w") as xml_file:
            subprocess.run(command, stdout=xml_file, check=True)
        print(f"Metadata fetched and saved to {xml_file_path}")

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

def process_assembly_summary(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("#"):
                continue
            columns = line.strip().split("\t")
            genome_id = columns[0]
            biosample_id = columns[2]
            genome_url = columns[19]
            relation_to_type_material = columns[21] if len(columns) > 21 else ""
            if relation_to_type_material.startswith("assembly"):
                genomic_file_url = download_genomic_file(genome_id, genome_url)
                fetch_biosample_metadata(biosample_id, genome_id)
                execute_dfast(genomic_file_url, genome_id)

# Example usage
# wget -O assembly_summary_refseq-20250116.txt https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt
# ln -s assembly_summary_refseq-20250116.txt assembly_summary_refseq.txt
assembly_summary_path = "/work1/mdatahub/private/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt"
process_assembly_summary(assembly_summary_path)
