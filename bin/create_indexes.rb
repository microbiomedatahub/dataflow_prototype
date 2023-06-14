#!/usr/bin/env ruby

require 'rubygems'
require 'nokogiri'
require 'erb'
require 'date'
require 'pp'
require 'pathname'
require "json"
require_relative 'mdatahub.rb'

# --- From bin/bioprojectxml2json.rb
require 'cgi'
require_relative 'lib_bioprojectxml2json.rb'
#input_path = 'C:\Users\iota_\Downloads\bioproject.xml'

root_dir = ARGV.length > 0 ? ARGV[0] : '.'
input_path = File.join(root_dir,'bioproject.xml')
out_path = File.join(root_dir,'bioproject.json')

output_ractor = Ractor.new(out_path) do |out_path|
    json = File.open(out_path, 'a')
    loop do
        l = Ractor.receive
        next unless l
        break if l == 1
        json << l
    end
    json.close
end

print Time.now, " Started\n"
File.delete(out_path) rescue nil
c = 0
reader = Nokogiri::XML::EnumParse
    .new(input_path, 'Package')
    .enumerator
reader.each do |elm|
    c += 1
    output_ractor.send(BPXml2JsonConverter.new(elm).to_json_with_meta + "\n")
end
output_ractor.send(1)
print "#{c} packages converted.\n"
print Time.now, " Finished\n"
---
#sleep(10)
##jsonl = '/work1/mdatahub/public/project/bioproject_0313.jsonl'
#jsonl = 'debug.jsonl'
#jsonl = 'bioproject_acc_test.jsonl'
#jsonl = '/work1/mdatahub/public/project/bioproject_0204.jsonl'
#jsonl = out_path

#index_project = 'mdatahub_index_project-dev.jsonl'
index_project = File.join(root_dir,'mdatahub_index_project.jsonl')
puts out_path
puts index_project
#input_dir = 'testdata/project'
input_dir =  File.join(root_dir,'project')

File.open(index_project ,mode = "w") do |out_p|
    IO.foreach(out_path) do |line|
        j = JSON.parse(line)
        #puts line
        #if bp = j['bioproject'] 
        if j['status'] == 'public'
            #bp = j
            acc = j['identifier']
            file = "#{input_dir}/#{acc2path(acc)}/#{acc}-biosampleset.xml" 
            warn file
            if File.exist? file
              bss = BioSampleSet.new(file)
              ann = bss.to_json_plus
              j['_annotation'] = ann
            else
              j['_annotation'] = BioSampleSet.new.json_plus_default
            end
            genome_count = 0        #FIXME: genome stats.
            has_analysis = false    #FIXME  genome stats.
            j['_annotation']['genome_count'] = genome_count
            j['has_analysis'] = has_analysis
            out_p.puts j.to_json
            #pp j.to_json
        else
            out_p.puts j.to_json
        end
    end
end
