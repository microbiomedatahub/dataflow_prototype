#!/usr/bin/env ruby

require 'fileutils'
require_relative 'mdatahub.rb'

root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfastqc/MAGoutput_dfastqc_218655'
#root_dir = '/work1/mdatahub/repos/dataflow_prototype/dfastqc/MAGoutput_dfastqc_218655/aa/output/GCA_001000715.1_ASM100071v1_genomic.fna'
puts "root_dir: #{root_dir}"


def asm_acc2path asm_acc
  a = asm_acc.gsub("GCA_","GCA").scan(/.{1,3}/)
  a[0..3].join("/")
end


#Dir.glob('**/*', 0, base: root_dir).each do |file|
Dir.glob('**/dqc_result.json', 0, base: root_dir).each do |file|
  file_path = File.join(root_dir, file)
  next unless file_path.match("")
  a = file_path.split('/')
  output_idx = a.index("output")
  asm_acc = a[output_idx + 1].gsub(/^(GCA_\d+\.\d+)_.+$/, '\1')
  asm_path = asm_acc2path asm_acc
  dir_path_src = File.dirname(file_path)
  basename = File.basename(dir_path_src)
  dir_path = File.join('/work1/mdatahub/public/genome', asm_path, asm_acc,'dfastqc')
  unless FileTest.exist?(dir_path)
    FileUtils.cp_r "#{dir_path_src}","#{dir_path}"
    puts "#{asm_acc}: #{dir_path_src}"
    puts "#{asm_acc}: #{dir_path}"
  end
end
