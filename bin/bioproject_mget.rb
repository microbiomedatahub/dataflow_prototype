#!/usr/bin/env ruby

require 'fileutils'
require 'pp'
require_relative 'mdatahub.rb'

input = ARGV.length > 0 ? ARGV[0] : '/work1/mdatahub/public/project/project_accessions'
out_dir = ARGV.length > 1 ? ARGV[1] : '/work1/mdatahub/public/project'
puts "input: #{input}"
puts "out_dir: #{out_dir}"

f = File.open(input)
f.each do |line|
    acc = line.chomp
    dir = acc2path acc
    m = acc.match(/^(PRJ[A-Z]+)([0-9]+)$/)
    acc_prefix = m[1]
    acc_num = m[2]
    dir = acc2path acc
    out_path = File.join(out_dir, dir)
    file = File.join(out_path, "#{acc}.xml")
    file_link = File.join(out_path, "#{acc}.dblink")
    file_sample = File.join(out_path, "#{acc}-biosampleset.xml")

    #puts file
    #puts file_link
    #puts file_sample
    FileUtils.mkdir_p(out_path) unless FileTest.exist?(out_path)
    unless FileTest.exist?(file)
        `efetch -db bioproject -id #{acc}  -mode xml > #{file}`
    end
    unless FileTest.exist?(file_link)
        `esearch -db bioproject -query '#{acc}' | elink -target biosample | efetch -format docsum | xtract -pattern DocumentSummary -element Accession >> #{file_link}`
    end
    unless FileTest.exist?(file_sample)
        `esearch -db bioproject -query '#{acc}' | elink -target biosample | efetch -mode xml > #{file_sample}`
    end
    puts acc
end
