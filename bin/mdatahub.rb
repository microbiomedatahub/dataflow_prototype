#!/usr/bin/env ruby

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

