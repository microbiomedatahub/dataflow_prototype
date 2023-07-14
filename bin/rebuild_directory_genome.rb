#!/usr/bin/env ruby
#
require 'fileutils'
require_relative 'mdatahub.rb'

root_dir = ARGV.length > 0 ? ARGV[0] : '/work1/mdatahub/public/project'
puts "root_dir: #{root_dir}"

# ディレクトリを再帰的に辿る
#Dir.glob('**/*', File::FNM_DOTMATCH, base: root_dir).each do |file|
Dir.glob('**/*', 0, base: root_dir).each do |file|
  # ファイルのパスを作る
  file_path = File.join(root_dir, file)
  #puts "#{file_path}"
  a = file.split('/')
  if a.count == 3 
    acc = a[2].gsub(/(\.|-).+$/,'')
    #puts acc
    file_path = File.join(root_dir, file)
    dir_after = acc2path acc
    dir_path = File.join(root_dir, dir_after) 
    
    #puts "#{acc}\t#{file}\t #{dir_path}"
    #FileUtils.mkdir_p(dir_path) unless FileTest.exist?(dir_path)
    #FileUtils.mv "#{file_path}","#{dir_path}"
  end
end
