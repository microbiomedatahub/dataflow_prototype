import os
import urllib.request
import subprocess

def asm_acc2path(asm_acc):
    parts = asm_acc.replace("GCF_", "GCF").split(".")[0]
    return "/".join([parts[i:i+3] for i in range(0, len(parts), 3)])

def create_genome_directory(genome_id):
    # Debug: Print genome_id
    print(f"Creating directory for genome_id: {genome_id}")

    # Set the environment variable for the base path
    os.environ['MDATAHUB_PATH_GENOME'] = '/tmp/genome'

    # Get the base path from the environment variable
    base_path = os.getenv('MDATAHUB_PATH_GENOME')

    # Ensure the genome_id follows the expected format
    if not genome_id.startswith("GCF_") or len(genome_id.split(".")) != 2:
        raise ValueError("Invalid genome ID format. Expected format: 'GCF_XXXXXXXXX.X'")

    # Construct the relative path using asm_acc2path
    relative_path = asm_acc2path(genome_id)

    # Construct the full directory path
    dir_path = os.path.join(base_path, relative_path, genome_id)

    # Check if the directory exists
    if not os.path.exists(dir_path):
        # Create the directory, including parent directories
        os.makedirs(dir_path)
        print(f"Directory created: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

    return dir_path

def download_genomic_file(genome_id, genome_url):
    # Extract the file name directly from genome_url
    original_file_name = genome_url.rstrip("/").split("/")[-1] + "_genomic.fna.gz"
    renamed_file_name = "genome.fna.gz"

    # Debug: Print genome_id
    print(f"Downloading file for genome_id: {genome_id}")

    # Create the directory for the genome ID
    target_dir = create_genome_directory(genome_id)

    # Define the download path
    download_path = os.path.join(target_dir, renamed_file_name)

    # Construct the full URL to the file
    file_url = genome_url + original_file_name

    # Download the file if it does not already exist
    if not os.path.exists(download_path):
        print(f"Downloading {file_url} to {download_path}...")
        urllib.request.urlretrieve(file_url, download_path)
        print(f"Download completed and saved as {download_path}")
    else:
        print(f"File already exists: {download_path}")

def fetch_biosample_metadata(biosample_id, genome_id):
    # Debug: Print genome_id
    print(f"Fetching metadata for genome_id: {genome_id}")

    # Create the directory for the genome ID
    target_dir = create_genome_directory(genome_id)

    # Define the XML file path
    xml_file_path = os.path.join(target_dir, f"{biosample_id}.xml")

    # Fetch the biosample metadata using the system command
    if not os.path.exists(xml_file_path):
        print(f"Fetching metadata for {biosample_id}...")
        command = ["efetch", "-db", "biosample", "-id", biosample_id, "-mode", "xml"]
        with open(xml_file_path, "w") as xml_file:
            subprocess.run(command, stdout=xml_file, check=True)
        print(f"Metadata fetched and saved to {xml_file_path}")
    else:
        print(f"Metadata file already exists: {xml_file_path}")

# Example usage
genome_id = "GCF_963396225.1"
genome_url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/963/396/225/GCF_963396225.1_CCUG_23930_T/"
download_genomic_file(genome_id, genome_url)
biosample_id = "SAMEA678330"
fetch_biosample_metadata(biosample_id, genome_id)
