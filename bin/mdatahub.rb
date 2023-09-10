#!/usr/bin/env ruby

require 'rubygems'
require 'nokogiri'
require 'erb'
require 'date'
require 'pp'
require 'pathname'
#require 'fileutils'
require "json"

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

def asm_acc2path asm_acc
  a = asm_acc.gsub("GCA_","GCA").scan(/.{1,3}/)
  a[0..3].join("/")
end


class BioSampleSet
  include Enumerable

  def initialize(xml='', params ={})
    @xml =xml  
  end

  def each
    xml_strs = []
    all = []
    IO.foreach(@xml) do |line|
      xml_strs.push(line.chomp)
      if line =~/\<\/BioSample\>/
        docs = xml_strs.join("\n").to_s
        bss = Nokogiri::XML(docs).css("BioSample")
          raise NameError, "biosample element not found" unless bss
        bss.each do |bs|
          all.push(bs)
        end
        #yield BioSample.new(docs)
        xml_strs = []
      end
    end
    all.each do |docs|
       yield BioSample.new(docs)
    end
  end

  def json_plus_default
{
'sample_count' => 0,
'sample_organism' => [],
'sample_taxid' => [],
'sample_ph' => [],
'sample_temperature' =>[],
'sample_host_organism' => [],
'sample_host_organism_id' => [],
'sample_host_disease' => [],
'sample_host_disease_id' => [],
'sample_host_location' => [],
'sample_host_location_id' => [],
'data_size' => '0.0 GB'
}
  end

  def to_json_plus
    ann = json_plus_default
    self.each_with_index do |biosample,i|
        ann['sample_count'] += 1
        ann['sample_organism'].push(biosample.organism)
        ann['sample_taxid'].push(biosample.taxid)
        biosample.sample_attributes.each do |att|
          hname = att[:harmonized_name]
          value = att[:value]
          case att[:display_name]
            when "pH", "fermentation pH","soil pH","surface moisture pH","wastewater pH","water pH"
                val = att[:value].delete("^(0-9|\.)")
                #puts "### #{att[:value]} --> #{val}"
                ann['sample_ph'].push(val.to_f) unless val ==""
                #ann['sample_ph'].push(att[:value])
            #when /temperature/i
            when "air temperature","annual and seasonal temperature","average temperature","depth (TVDSS) of hydrocarbon resource temperature","dew point","fermentation temperature","food stored by consumer (storage temperature)","host body temperature","hydrocarbon resource original temperature","mean annual temperature","mean seasonal temperature","pour point","sample storage temperature","sample transport temperature","soil temperature","study incubation temperature","surface temperature","temperature","temperature outside house","wastewater temperature"
                #val = att[:value].gsub(" C","")
                #att[:value].class
                #val = [att[:value].to_f].grep(Numeric).first
                #TODO: Fahrenheit → Celsius
                val = att[:value].delete("^(0-9|\.)")
                #puts "### #{att[:value]} --> #{val}"
                #pp "###{val}###"
                ann['sample_temperature'].push(val.to_f) unless val == ""
            when "host"
                ann['sample_host_organism'].push(att[:value])
            when "disease","fetal health status", "host disease", "health","health status","host health state","host of the symbiotic host disease status","outbreak","study disease"
                ann['sample_host_disease'].push(att[:value])
            when /location/i 
            #when "birth location","geo loc exposure","geographic location","host recent travel location"
            # "ethnicity"
            # "race"
            # "latitude and longitude"
            # "food distribution point geographic location","food product origin geographic location" 
                ann['sample_host_location'].push(att[:value])
            end
        end
    end
       #pp  ann['sample_temperature']
       ann['sample_ph_range'] = { "min"=> ann['sample_ph'].min, "max" => ann['sample_ph'].max }
       ann['sample_temperature_range'] = { "min"=>  ann['sample_temperature'].min, "max" => ann['sample_temperature'].max }
       #warn ann['sample_ph_range']
       #warn ann['sample_temperature_range'] 
       ann['sample_taxid'].uniq!
       ann['sample_host_organism'].uniq!
       ann['sample_host_disease'].uniq!
       ann['sample_host_location'].uniq!
       ann['sample_organism'].uniq!
       ann.delete('sample_ph')
       ann.delete('sample_temperature')
    #pp ann
    ann
  end

  def to_json
    self.each_with_index do |biosample,i|
      #puts biosample.to_json
      pp biosample.to_object
    end
  end
end

class BioSample

   def initialize(bs)
       @biosample = bs
    if @biosample.attribute("id").nil?
      @ddbj = true
    else
      @ddbj = false
    end
  end

  def id
    if @ddbj
      nil
    else
      @biosample.attribute("id").value
    end
    # @biosample.attribute("id").nil? ?
    #         '' : @biosample.attribute("id").value
  end

  def accession
    if @ddbj
      @biosample.at_css('Ids > Id[namespace="BioSample"]').inner_text
    else
      #@biosample.attribute("accession").value
      if @biosample.at_css('Ids > Id[db="BioSample"]').nil?
        nil
      else
        @biosample.at_css('Ids > Id[db="BioSample"]').inner_text
      end
    end
  end

  def access
    @biosample.attribute("access").value
  end

  def publication_date
    if  @biosample.attribute("publication_date").nil?
      ''
    else
      @biosample.attribute("publication_date").value
    end
  end

  def last_update
    @biosample.attribute("last_update").value
  end

  def title
    if @ddbj 
      @biosample.css('Description > SampleName' ).inner_text
    else
      @biosample.css('Description > Title' ).inner_text
    end
  end

  def comment
    if @ddbj
      @biosample.css('Description > Title' ).inner_text
    else
      #exception: SAMN00000186
      if @biosample.at_css('Description > Comment > Paragraph' ).nil?
        ''
      else
        @biosample.at_css('Description > Comment > Paragraph' ).inner_text
      end
    end
  end 

  def organism
    if @ddbj 
      @biosample.css('Organism > OrganismName').inner_text
    else
      @biosample.css('Description > Organism').attribute('taxonomy_name').value
    end
  end

  def taxid
    @biosample.css('Description > Organism').attribute('taxonomy_id').value
  end

  def model
    @biosample.css('Models > Model').inner_text
  end

  def owner
    @biosample.css('Owner > Name').inner_text
  end

  def to_object
      {
          :accession => self.accession,
          :publication_date => self.publication_date,
          :last_update => self.last_update,
          :attributes => self.sample_attributes,
          #:xml => @xml
          :xml => @biosample.to_xml
      }
  end
  def to_tsv
     [self.accession, self.publication_date, self.last_update ].join("\t")
  end

  def to_json
      {
          "identifier": self.id
      }
  end

  def to_ttl
    erb = accession ? self.template : self.template_blank
    puts erb.result(binding)
  end

  def template
    tpl = <<EOF
<http://identifiers.org/biosample/<%= self.accession %>>
  rdf:type insdc:BioSample ;
  rdfs:label "<%= self.title %>" ;
  rdfs:comment "<%= self.comment -%>" ;
  insdc:organism "<%= self.organism -%>" ;
  obo:RO_0002162 <http:identifiers.org/taxonomy/<%= self.taxid -%>> ; #RO:in taxon
  owl:sameAs <http://trace.ddbj.nig.ac.jp/BSSearch/biosample?acc=<%= self.accession %>> ;
  owl:sameAs <http://www.ebi.ac.uk/ena/data/view/<%= self.accession %>> ;
  owl:sameAs <http://www.ncbi.nlm.nih.gov/biosample?term=<%= self.accession %>> ;
  biosample:model "<%= self.model %>" ;
  biosample:owner "<%= self.owner %>" ;
<% self.sample_attributes.each do |attribute| -%>
  biosample:<%= attribute[:name] %> "<%= attribute[:value] %>" ;
<% end -%>
<% self.sample_ids.each do |id| -%>
  biosample:dblink "<%= id[:name] %>:<%= id[:value] %>" ;
<% end -%>
<% self.sample_links.each do |link| -%>
  biosample:db_xref "<%= link[:name] %>:<%= link[:value] %>" ;
<% end -%>
  biosample:access "<%= self.access %>" ;
  biosample:publication_date "<%= self.publication_date %>" ;
  biosample:last_update "<%= self.last_update %>" .
EOF
  ERB.new(tpl, nil, '-')
  end

  def template_blank
                tpl = <<EOF
[
  rdf:type insdc:BioSample ;
  rdfs:label "<%= self.title %>" ;
  rdfs:comment "<%= self.comment -%>" ;
  insdc:organism "<%= self.organism -%>" ;
  obo:RO_0002162 <http:identifiers.org/taxonomy/<%= self.taxid -%>> ; #RO:in taxon
  biosample:access "<%= self.access %>" ;
  biosample:publication_date "<%= self.publication_date %>" ;
  biosample:last_update "<%= self.last_update %>" ;
  biosample:model "<%= self.model %>" ;
  biosample:owner "<%= self.owner %>" ;
<% self.sample_attributes.each do |attribute| -%>
  biosample:<%= attribute[:name] %> "<%= attribute[:value] %>" ;
<% end -%>
<% self.sample_ids.each do |id| -%>
  biosample:dblink "<%= id[:name] %>:<%= id[:value] %>" ;
<% end -%>
<% self.sample_links.each do |link| -%>
  biosample:db_xref "<%= link[:name] %>:<%= link[:value] %>" ;
<% end -%>
  biosample:access "<%= self.access %>" ;
  biosample:publication_date "<%= self.publication_date %>" ;
  biosample:last_update "<%= self.last_update %>" ;
]
.
EOF
  ERB.new(tpl, nil, '-')
        end

  def sample_attributes
    #      doc.xpath("/BioSample/Attributes/Attribute").each do |element|
    #         children = element.children.to_s
    #         attribute_name = element.attribute("attribute_name").value
    #         harmonized_name = element.attribute("harmonized_name").nil? ?
    #              '' : element.attribute("harmonized_name").value
    #         display_name = element.attribute('display_name').nil? ?
    #              '' : element.attribute("display_name").value
    #         #puts [accession,id,attribute_name,harmonized_name,display_name,children].join("\t")
    #         puts "biosample:attributes##{URI.escape(attribute_name)}>\t\"#{children.gsub('"','\\"')}\" ;"
    #      end
    @biosample.css('Attributes > Attribute').map do |node|
        hname = node.attribute('harmonized_name') ? node.attribute('harmonized_name').value : ""
        dname = node.attribute('display_name') ? node.attribute('display_name').value : ""
                        {
      name: self.uri_escaped(node.attribute('attribute_name').value),
      value:  self.ttl_escaped(node.inner_text.to_s),
      harmonized_name: self.uri_escaped(hname),
      display_name: self.uri_escaped(dname)
      }
    end
  end

  def sample_ids
    ids = @biosample.css('Ids > Id').map do |node|
      children = node.inner_text.to_s
      if @ddbj
                                {
        name: self.uri_escaped(node.attribute("namespace").value),
        value: self.ttl_escaped(node.inner_text.to_s)
        }
      else
        db = node.attribute("db").nil? ? node.attribute("db_label").value : node.attribute("db").value 
        {
        name: self.uri_escaped(db),
        value: self.ttl_escaped(node.inner_text.to_s)
        }
      end
    end
    #      doc.xpath("/BioSample/Ids/Id").each do |element|
    #         children = element.children.to_s
    #         #attribute_name = element.attribute("namespace").value #DDBJ
    #         attribute_name = element.attribute("namespace") ? attribute_name = element.attribute("namespace").value : attribute_name = element.attribute("db").value
    #         puts "\tdcterms:identifier\t\"#{URI.escape(attribute_name)}:#{children}\" ;"
    #      end
  end

  def sample_links
    #      #doc.xpath('/BioSample/Links/Link').each do |element| # DDBJ
    #      doc.xpath('/BioSample/Links/Link[@type="url"]').each do |element| #NCBI
    #         children = element.children.to_s
    #         attribute_name = element.attribute("label").value #DDBJ
    #         #puts "\t<http://ddbj.nig.ac.jp/ontologies/biosample/link##{URI.escape(attribute_name)}>\t\"#{children}\" ;"
    #         puts "\tdcterms:identifier\t\"#{URI.escape(attribute_name)}:#{children}\" ;"
    #      end
    if @ddbj
      @biosample.css('Links > Link').map do |node|
        {
        name: self.uri_escaped(node.attribute("label").value),
        value: self.ttl_escaped(node.inner_text.to_s)
        }
      end
    else
      @biosample.css('Links > Link[type="url"]').map do |node|
        label = node.attribute("label").nil? ? node.attribute("target").value : node.attribute("label").value
        {
        name: self.uri_escaped(label),
        value: self.ttl_escaped(node.inner_text.to_s)
        }
      end
    end
  end 

        def uri_escaped(string)
            require 'uri'
            URI.encode_www_form_component(string)
        end
        # seeAlso: http://rdf.greggkellogg.net/yard/RDF/Writer.html#escaped-instance_method
  def ttl_escaped(string)
    string.gsub('\\', '\\\\\\\\').
    gsub("\b", '\\b').
    gsub("\f", '\\f').
    gsub("\t", '\\t').
    gsub("\n", '\\n').
    gsub("\r", '\\r').
    gsub('"', '\\"')
  end

  # TODO
  def related_link
    @study.css("RELATED_LINK").map do |node|
      { db: node.css("DB").inner_text,
        id: node.css("ID").inner_text,
      label: node.css("LABEL").inner_text }
    end
  end
end

class MAG
  def initialize(base, params ={})
    if base.has_key?("bioproject")
      @base = base["bioproject"]
    else
      @base =base
    end
    @params = params
  end
  
  def annotate
    File.open(@params[:dfast_qc]) do |f|
        dfast_qc = JSON.load(f)
        @base['_annotation'].merge!(dfast_qc['cc_result'])
    end
    @base["type"] = "genome"
    @base["identifier"] = @params[:id]
    @base["organism"] = @params[:organism]
    @base["title"] = ""
    @base["description"] = ""
    @base["data_type"] = "low-quality MAG" #TODO
    @base["dateCreated"] = today
    @base["dateModified"] = today
    @base["data_source"] =  "INSDC"
    @base["_annotation"]["sample_count"] = 1 #TODO
    @base["_annotation"]["sample_organism"] = [] #TODO
    @base["_annotation"]["sample_taxid"] = [] #TODO
    #@base["_annotation"]["sample_environment"] = "soil" #TODO
    # dfast由来
    # dfast_qc由来

    @base
  end

  def today
    require "date"
    d = Date.today
    str = d.strftime("%Y-%m-%d")
  end 
end
