#!/usr/bin/env ruby

require 'date'
d = Date.today
today = d.strftime("%Y%m%d")

print Time.now, " Started\n"
`esearch -db bioproject -query 'txid408169[Organism:exp] AND "Primary submission"[Filter]' | efetch -format xml | xtract -pattern DocumentSummary -element Project_Acc > project_accessions-#{today}`
#system("esearch -db bioproject -query 'txid408169[Organism:exp] AND \"Primary submission\"[Filter]' | efetch -format docsum | xtract -pattern DocumentSummary -element Project_Acc > project_acc")
print Time.now, " Finished\n"
