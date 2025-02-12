#!/bin/bash

HEAD="Content-Type:application/x-ndjson"
URL="localhost:9200/_bulk"

for i in `ls ../mdatahub_index_project-20230612.jsonl_part_*`
do
	#echo "curl -s -H $HEAD -XPOST $URL --data-binary \"@$i\""
        curl -s -H $HEAD -XPOST $URL --data-binary "@$i" > $i.logs
done
