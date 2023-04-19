# dataflow_prototype

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
