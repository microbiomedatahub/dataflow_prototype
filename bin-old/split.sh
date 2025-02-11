#!/bin/bash

maxsize=50000000
splitlen=50000
recursivelen=1000

split -l $splitlen -a 3 -d /work1/mdatahub/repos/dataflow_prototype/mdatahub_index_genome-20230910.jsonl bulk_import/bp_jsonl_part_

for i in *
do
        fsize=$(wc -c <"$i")

        if [ $fsize -ge $maxsize ]; then
                fname="${i}_part_"
                split -l $recursivelen -a 3 -d $i $fname

        fi

done
