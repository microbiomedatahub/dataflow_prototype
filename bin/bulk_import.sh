#!/bin/bash

HEAD="Content-Type:application/x-ndjson"
URL="localhost:9200/_bulk"

for i in bp_jsonl_part_*
do
        curl -s -H $HEAD -XPOST $URL --data-binary "@$i" > /mnt/sra/xml/logs/bp/$i
done