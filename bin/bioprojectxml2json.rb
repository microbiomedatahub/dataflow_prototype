require 'json'
require 'nokogiri'
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
