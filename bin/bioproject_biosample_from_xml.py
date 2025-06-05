import gzip
import argparse
from lxml import etree

def extract_biosample_bioproject_links(xml_gz_path, output_path):
    with gzip.open(xml_gz_path, "rb") as f_in:
        context = etree.iterparse(f_in, events=("end",), tag="BioSample")

        with open(output_path, "w", encoding="utf-8") as out:
            for event, elem in context:
                biosample_accession = elem.get("accession")

                links_elem = elem.find("Links")
                if links_elem is not None:
                    for link in links_elem.findall("Link"):
                        if link.get("target") == "bioproject":
                            bioproject_label = link.get("label")
                            if biosample_accession and bioproject_label:
                                out.write(f"{biosample_accession}\t{bioproject_label}\n")

                # メモリ解放
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

if __name__ == "__main__":
    """
    biosample_set.xml.gzからBioSampleとBioProjectのリンクを抽出し、TSV形式で保存するスクリプト
    使用方法:
    python bioproject_biosample_from_xml.py -i biosample_set.xml.gz -o output.tsv
    """
    parser = argparse.ArgumentParser(description="Extract BioSample-bioproject links from biosample_set.xml.gz")
    parser.add_argument("-i", "--input", required=True, help="Input .xml.gz file path")
    parser.add_argument("-o", "--output", required=True, help="Output .tsv file path")
    args = parser.parse_args()

    extract_biosample_bioproject_links(args.input, args.output)
