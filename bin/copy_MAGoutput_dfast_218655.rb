#!/usr/bin/env ruby

require 'fileutils'
require_relative 'mdatahub.rb'

root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfast/MAGoutput_dfast_218655'
#root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfast/MAGoutput_dfast_218655/aa'
#root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfast/MAGoutput_dfast_218655/aa/output/GCA_001000705.1_ASM100070v1_genomic.fna'
#root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfast/MAGoutput_dfast_218655/aa/output/GCA_001000715.1_ASM100071v1_genomic.fna'
puts "root_dir: #{root_dir}"


def asm_acc2path asm_acc
  a = asm_acc.gsub("GCA_","GCA").scan(/.{1,3}/)
  a[0..3].join("/")
end


#Dir.glob('**/*', 0, base: root_dir).each do |file|
Dir.glob('**/statistics.txt', 0, base: root_dir).each do |file|
  file_path = File.join(root_dir, file)
  next unless file_path.match("")
  #puts "#{file_path}"
  a = file_path.split('/')
  output_idx = a.index("output")
  asm_acc = a[output_idx + 1].gsub(/^(GCA_\d+\.\d+)_.+$/, '\1')
  asm_path = asm_acc2path asm_acc
  dir_path_src = File.dirname(file_path)
  basename = File.basename(dir_path_src)
  dir_path = File.join('/work1/mdatahub/public/genome', asm_path, asm_acc,'dfast')
  #dir_path = File.join('/work1/mdatahub/public/genome', asm_path, asm_acc)
  #dir_path_b = File.join('/work1/mdatahub/public/genome', asm_path, asm_acc, basename)
  #dir_path_a = File.join('/work1/mdatahub/public/genome', asm_path, asm_acc, 'dfast')
  unless FileTest.exist?(dir_path)
    FileUtils.cp_r "#{dir_path_src}","#{dir_path}"
    puts "#{asm_acc}: #{dir_path}"
    #FileUtils.mv "#{dir_path_b}","#{dir_path_a}"
    #puts "#{asm_acc}: #{dir_path_b}"
    #puts "#{asm_acc}: #{dir_path_a}"
  end
#  if basename = a[output_idx + 5] 
#     FileUtils.mkdir_p(dir_path) unless FileTest.exist?(dir_path)
#     #puts "#{asm_acc}: #{dir_path}"
#     if file_path.match(/_genomic.fna.gz/)
#       new_file_path = File.join(dir_path, 'genome.fna.gz')
#       puts new_file_path
#       FileUtils.cp "#{file_path}","#{new_file_path}"
#     else
#       new_file_path = File.join(dir_path, basename)
#       puts new_file_path
#       FileUtils.cp "#{file_path}","#{new_file_path}"
#     end
#  end
end
