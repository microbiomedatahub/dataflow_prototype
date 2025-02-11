#!/usr/bin/env ruby

require 'fileutils'
require_relative 'mdatahub.rb'

#root_dir = ARGV.length > 0 ? ARGV[0] : '/work1/mdatahub/public/genome'
#root_dir = ARGV.length > 0 ? ARGV[0] : '/work1/mdatahub/repos/dataflow_prototype/genomes/all/GCA'
root_dir = '/work1/mdatahub/repos/dataflow_prototype/genomes/all/GCA'
#root_dir = '/tmp/genomes'
puts "root_dir: #{root_dir}"

#Dir.glob('**/*', File::FNM_DOTMATCH, base: root_dir).each do |file|
Dir.glob('**/*', 0, base: root_dir).each do |file|
  file_path = File.join(root_dir, file)
  next unless file_path.match("GCA_")
  #puts "#{file_path}"
  a = file_path.split('/')
  gca_idx = a.index("GCA")
  asm_acc = a[gca_idx + 4].gsub(/^(GCA_\d+\.\d+)_.+$/, '\1')
  dir_path = File.join('/work1/mdatahub/public/genome', a[gca_idx],a[gca_idx+1],a[gca_idx+2],a[gca_idx+3], asm_acc)
  #acc = a[2].gsub(/(\.|-).+$/,'')
  #dir_after = acc2path acc
  if basename = a[gca_idx + 5] 
     FileUtils.mkdir_p(dir_path) unless FileTest.exist?(dir_path)
     #puts "#{asm_acc}: #{dir_path}"
     if file_path.match(/_genomic.fna.gz/)
       new_file_path = File.join(dir_path, 'genome.fna.gz')
       puts new_file_path
       FileUtils.cp "#{file_path}","#{new_file_path}"
     else
       new_file_path = File.join(dir_path, basename)
       puts new_file_path
       FileUtils.cp "#{file_path}","#{new_file_path}"
     end
  end
###    else
###    #GCA_001916705.1_ASM191670v1_genomic.fna.gz
###    #FileUtils.mv "#{file_path}","#{dir_path}"
###  end
end
