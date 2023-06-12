#!/usr/bin/env ruby
#
require 'fileutils'

def acc2path acc
  m = acc.match(/^(PRJ[A-Z]+)([0-9]+)$/)
  acc_prefix = m[1]
  acc_num = m[2]
  dir =""
  if acc_num.length == 6
      dir = acc_num.slice(0,3)
      dir2= acc
  elsif acc_num.length == 5
      dir = "0" + acc_num.slice(0,2)
      dir2= acc_prefix + "0" + acc_num
  elsif acc_num.length == 4
      dir = "00" + acc_num.slice(0,1)
      dir2= acc_prefix + "00" + acc_num
  elsif acc_num.length == 3
      dir = "000"
      dir2 = acc_prefix + "000" + acc_num
  elsif acc_num.length == 2
      dir = "000"
      dir2 = acc_prefix + "0000" + acc_num
  elsif acc_num.length == 1
      dir = "000"
      dir2 = acc_prefix + "00000" + acc_num
  else
      #dir = acc_num.slice(0,3)
      exit "undefined directory: #{acc_num}"
  end
  path ="#{acc_prefix}/#{dir}/#{dir2}"
end


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
    
    #puts "#{acc}: #{acc2path acc}"
    FileUtils.mkdir_p(dir_path) unless FileTest.exist?(dir_path)
    FileUtils.mv "#{file_path}","#{dir_path}"
    #command = "mv #{file_path} #{dir_path}"
    #puts command
    #puts `command`
  end
end
