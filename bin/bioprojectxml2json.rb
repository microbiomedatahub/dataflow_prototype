require 'json'
require 'nokogiri'
require 'cgi'

#
# bioproject.xmlをjsonに変換するクラス
#
class BPXml2JsonConverter
    #
    # コンストラクタ
    #
    # @param [String] bp_xml bioproject.xml から切り出したPackageエレメント
    #
    def initialize(bp_xml)
        begin
            xml = Nokogiri::XML(bp_xml)
        rescue
            print "#{bp_xml[0..100]}\n(#{xml})"
        end

        @hash = {
            'type' => 'bioproject',
            'identifier' => xml.xpath('.//ProjectID/ArchiveID/@accession')[0],
            'organism' => xml.xpath('.//Project/Project/ProjectDescr/Name')[0]&.text,
            'title' => xml.xpath('.//Project/Project/ProjectDescr/Title')[0]&.text,
            'description' => xml.xpath('.//Project/ProjectDescr/Description')[0]&.text,
            'data type' =>  xml.xpath('.//ProjectTypeSubmission/ProjectDataTypeSet/DataType')[0]&.text,
            'organization' => xml.xpath('.//Submission/Description/Organization/Name')[0]&.text,
            'publication' => xml.xpath('.//Project/ProjectDescr/Publication').map do |elm|
                {'id' => elm['id'], 'Title' => elm.xpath('.//Title')&.text}
            end,
            'properties' => nil,
            'dbXrefs' => xml.xpath('.//Project/ProjectDescr/LocusTagPrefix').map do |elm|
                elm['biosample_id']
            end,
            'distribution' => nil,
            'Download' => nil,
            'status' => xml.xpath('.//Project/Submission/Description/Access')[0]&.text,
            'visibility' => nil
        }
        # 以下、Pythonコードからコピー
        # Todo: 以下ElasticSearchの項目がDate型なため空の値を登録できない（レコードのインポートがエラーとなりスキップされる）
        submission = xml.xpath('.//Project/Submission')[0]
        if submission
            @hash['dateCreated'] = submission['submitted'] if submission['submitted']
            @hash['dateModified'] = submission['last_update'] if submission['last_update']
        end
        date_published = xml.xpath('.//Project/ProjectDescr/ProjectReleaseDate')[0]&.text
        @hash['datePublished'] = date_published if date_published
    end

    #
    # XMLエレメントを所定の形式のjsonに変換します。
    #
    def to_json
        @hash.to_json
    end

    #
    # XMLエレメントから所定のメタ情報のjsonを出力します。
    #
    def meta_json
        {index: {_index: 'bioproject', _type: 'metadata', _id: @hash['identifier']}}.to_json
    end

    #
    # XMLエレメントをメタ情報と所定の形式のjsonのセットで出力します。
    #
    def to_json_with_meta
        "#{meta_json}\n#{to_json}"
    end
end

#
# Python の etree.iterparse と類似の機能を提供するクラス
#
class Nokogiri::XML::EnumParse
    class SAXDoc < Nokogiri::XML::SAX::Document
        def initialize(tag)
            @tag = tag
            @buf = ''
            @layer = 0
        end

        def start_element(name, attrs)
            @layer += 1 if name == @tag
            return if @layer == 0
            if attrs.empty?
                @buf << "<#{name}>"
            else
                attr_pairs = attrs.map do |a|
                    a[0] + '="' + a[1].gsub('"', '%22') + '"'
                end.join(' ')
                @buf << "<#{name} #{attr_pairs}>"
            end
        end

        def end_element(name)
            return if @buf.empty?
            @layer -= 1 if name == @tag
            @buf << "</#{name}>" if @layer > 0
            if @layer == 0 && name == @tag
                @buf << "</#{name}>"
                Fiber.yield(@buf)
                @buf = ''
            end
        end

        def characters(string)
            @buf << CGI.escapeHTML(string) if @layer > 0
        end
    end

    #
    # コンストラクタ
    #
    # @param [String] file_path XMLファイルのパス
    # @param [String] tag XMLファイルから分割して切り出すタグ
    #
    def initialize(file_path, tag)
        raise ArgumentError, 'file_path is not set.' unless file_path.is_a?(String)
        raise ArgumentError, 'tag is not set.' unless tag.is_a?(String)

        @fiber = Fiber.new do
            Nokogiri::XML::SAX::Parser.new(SAXDoc.new(tag)).parse(File.open(file_path)) {|ctx| ctx.recovery = true}
            Fiber.yield(nil)
        end
    end

    #
    # 指定された tag の XMLエレメントを順次処理する Enumerator オブジェクトを返します
    #
    # @return [Enumerator] XMLエレメントを順次処理する Enumerator オブジェクト
    #
    def enumerator
        Enumerator.new do |y|
            loop do
                res = @fiber.resume
                break unless res
                y << res
            end
        end
    end
end

out_path = 'bioproject.json'

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
    .new('C:\Users\iota_\Downloads\bioproject.xml', 'Package')
    .enumerator
reader.each do |elm|
    c += 1
    output_ractor.send(BPXml2JsonConverter.new(elm).to_json_with_meta + "\n")
end
output_ractor.send(1)
print "#{c} packages converted.\n"
print Time.now, " Finished\n"
