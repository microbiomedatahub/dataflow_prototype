require 'json'
require 'sqlite3'
require 'rgl/adjacency'
require 'rgl/traversal'
require 'rgl/dot'
require_relative 'mdatahub.rb'

#----------------------------------------
# 再帰的に Bioproject→Bioproject のリンクを追加

# dblink
def bioproject_path(db,sql,query,dblink)
  results = db.execute(sql, [query])
  #puts "##result.size #{results.size}"
  unless results.empty?
    results.each do |row|
      #next if query == row[0]
      #puts "##query #{query}, row[0] #{row[0]}, row[1] #{row[1]}"
      dblink['bioproject-tree-path'].push(row[0])
      dblink['umbrella-bioproject-count'] += 1
      bioproject_path(db, sql, row[0], dblink)
    end
  end
  dblink
end

def bioproject_related_biosample(arr)
  result = arr.each_with_object(Hash.new { |h, k| h[k] = [] }) do |(bp, bs), hash|
    hash[bs] << bp
  end  
  result
end
# graph
#def add_graph(db, sql, sql_s, query, graph)
#  results = db.execute(sql, [query])
#
#  unless results.empty?
#    results.each do |row|
#      graph.add_edge(row[0], row[1])
#
#      ### Umbrella BP/BS はなかった
#      # results_s = db.execute(sql_s, [row[0]])
#      # unless results.empty?
#      #   results_s.each do |row2|
#      #     # filtered_data['biosample'].push(row)
#      #     graph.add_edge(row2[0], row2[1])
#      #   end
#      # end
#      ###
#
#      graph = add_graph(db, sql, sql_s, row[0], graph)
#    end
#  end
#
#  graph
#end

#graph_mag
##----------------------------------------
## 再帰的に JSON 用ノード／リンク情報を追加
#def add_graph_mag(db, sql, sql_s, query, graph_mag)
#  results = db.execute(sql, [query])
#
#  unless results.empty?
#    results.each do |row|
#      graph_mag['nodes'].push({ 'id' => row[0], 'group' => 1 })
#      graph_mag['links'].push({ 'source' => row[0], 'target' => row[1], 'value' => 1 })
#
#      graph_mag = add_graph_mag(db, sql, sql_s, row[0], graph_mag)
#    end
#  end
#
#  graph_mag
#end

#----------------------------------------
# 入力ファイルパス
file_path = 'genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt'

# ヘッダー行を保存する変数
headers = []

# SQLite データベースファイルのパス
#db_path = 'ddbj_dblink_bpbs.sqlite'
db_path = 'relation.db'

# SQLite データベースに接続
db = SQLite3::Database.new(db_path)

#----------------------------------------
# SQL クエリ: Umbrella Bioproject → Bioproject
sql = <<-SQL
  SELECT distinct *
  FROM bioproject_umbrella2bioproject
  WHERE field2 = ? ;
SQL

# SQL クエリ: Bioproject → BioSample
sql_s = <<-SQL
  SELECT distinct * 
  FROM biosample_bioproject
  WHERE field2 = ? ;
SQL

#----------------------------------------
# graph
## RGL グラフオブジェクト (未使用だがロジックに残す)
#graph = RGL::DirectedAdjacencyGraph.new

#----------------------------------------
# メインループ: assembly_summary_genbank.txt の各行を処理
File.open(file_path, 'r') do |file|
  file.each_line.with_index do |line, index|
    # 1行目はスキップ
    next if index == 0
    # 2行目 (ヘッダー行) を取得
    if index == 1
      headers = line.strip.sub(/^#/, '').split("\t").map { |header| header.strip }
      next
    end
    # データ行をタブ区切りでパースし、ハッシュ化
    fields = line.strip.split("\t")
    data = headers.zip(fields).to_h
    # excluded_from_refseq カラムに "derived from metagenome" を含む行のみ処理
    if data['excluded_from_refseq']&.include?('derived from metagenome')

# output_public_path
#      #----------------------------
#      # 出力 JSON ファイルパスを生成
#      asm_path = asm_acc2path(data['assembly_accession'])
#      output_file_genome_path = File.join(
#        'public/genome',
#        asm_path,
#        data['assembly_accession'],
#        'dblink.json'
#      )


# graph_mag
#      # 初期ノード／リンクを準備
#      graph_mag = {
#        'nodes' => [
#          { 'id' => data['bioproject'],        'group' => 2 },
#          { 'id' => data['biosample'],         'group' => 3 },
#          { 'id' => data['assembly_accession'], 'group' => 4 }
#        ],
#        'links' => [
#          { 'source' => data['bioproject'],        'target' => data['biosample'],         'value' => 1 },
#          { 'source' => data['biosample'],         'target' => data['assembly_accession'], 'value' => 1 }
#        ]
#      }

# dblink
    dblink = {
      'assembly-accession' => data['assembly_accession'],
      'assembly-bioproject'         => data['bioproject'],
      'assembly-biosample'          => data['biosample'],
      'umbrella-bioproject-count'   => 0,
      'biosample-count'   => 0,
      'bioproject-tree-path'    => [],
      #'bioproject-related-biosample-arr'       => [],
      #'bioproject-related-biosample'       => {}
      'bioproject-related-biosample'       => []
    }

# filtered_data
#      # フィルタ済みデータ保持用ハッシュ
#      filtered_data = {
#        'assembly': {
#          'assembly_accession' => data['assembly_accession'],
#          'bioproject'         => data['bioproject'],
#          'biosample'          => data['biosample'],
#          'taxid'              => data['taxid'],
#          'species_taxid'      => data['species_taxid'],
#          'organism_name'      => data['organism_name']
#        },
#        'bioproject' => [],
#        'biosample'  => []
#      }

      #----------------------------
      # Bioproject → UmbrellaBioproject の取得 (親子関係)
      dblink['bioproject-tree-path'].push(data['bioproject'])
      bioproject_path(db, sql, data['bioproject'], dblink)

#      results = db.execute(sql, [data['bioproject']])
#      if results.empty?
#        # 該当なし：出力せずスキップ
#      else
          
# graph
#        # RGL グラフ上にも Bioproject→BioSample のリンクを追加
#        graph.add_edge(data['bioproject'], data['biosample'])

#        results.each do |row|

          #dblink['bioproject-tree-path'].push(row)
          #dblink = bioproject_path(db, sql, sql_s, row[0], dblink)
#          bioproject_path(db, sql, sql_s, row[0], dblink)

# graph
#          # row[0] が親 BP、row[1] が子 BP（テーブル構成に依存）
#          graph.add_edge(row[0], row[1])
#
#          # 再帰的に Bioproject→Bioproject をたどり RGL グラフへ追加
#          graph = add_graph(db, sql, sql_s, row[0], graph)

# filtered_data
#          # filtered_data に Bioproject ペアを追加
#          filtered_data['bioproject'].push(row)

# graph_mag          
#          # graph_mag にノード／リンク情報を追加
#          graph_mag['nodes'].push({ 'id' => row[0], 'group' => 1 })
#          graph_mag['links'].push({ 'source' => row[0], 'target' => row[1], 'value' => 1 })
#
#          # 再帰的に JSON 用ノード／リンクを追加
#          graph_mag = add_graph_mag(db, sql, sql_s, row[0], graph_mag)
          
#        end
#      end

      #----------------------------
      # Bioproject → BioSample の取得

      dblink['bioproject-tree-path'].each do |bp|
          results_s = db.execute(sql_s, [bp])
          unless results_s.empty?
              results_s.each do |row|
                   #next if data['biosample'] == row[1] #TODO:あとで復活させるかも
                   dblink['biosample-count'] += 1
                   #dblink['bioproject-related-biosample-arr'].push(row)
                   dblink['bioproject-related-biosample'].push(row)
              end               
          end   
      end
      #dblink['bioproject-related-biosample'] = bioproject_related_biosample(dblink['bioproject-related-biosample-arr'])    



      
#      results_s = db.execute(sql_s, [data['bioproject']])
#
#      unless results_s.empty?
#        results_s.each do |row|
          # row[0] が BP、row[1] が BS

#          dblink['bioproject-related-biosample'].push(row)
          
# graph
#          graph.add_edge(row[0], row[1])


# filtered_data
#          # filtered_data に Biosample ペアを追加
#          filtered_data['biosample'].push(row)

# graph_mag
#          # graph_mag にノード／リンク追加
#          graph_mag['nodes'].push({ 'id' => row[1], 'group' => 3 })
#          graph_mag['links'].push({ 'source' => row[0], 'target' => row[1], 'value' => 1 })
          #
#        end
#      end
      # Bioproject → BioSample の取得

# BP-BS 絞り込み条件
#      #----------------------------
#      # 出力判定: Bioproject→Bioproject のリンク数が 2 未満ならスキップ
#      #next if results.size < 1
#      next if results.size < 2
#
#      #----------------------------
#      # 出力: ファイルパスをコメント行で表示

### 出力
      #puts dblink.to_json
      next if dblink['umbrella-bioproject-count'] == 0
      next if dblink['biosample-count'] < 2
      puts [
        dblink['assembly-accession'],
        dblink['assembly-bioproject'],
        dblink['assembly-biosample'],
        dblink['umbrella-bioproject-count'],
        dblink['biosample-count'],
        dblink['bioproject-tree-path'].last,
        dblink['bioproject-tree-path'].to_s
        #dblink['bioproject-related-biosample'].to_s
      ].join("\t")


#  "bioproject-tree-path": [
#    [ "PRJNA63549", "PRJNA63555" ],
#    [ "PRJNA20823", "PRJNA63549" ]
#  ],
#  "bioproject-related-biosample": [
#    [ "PRJNA63555", "SAMN02954274" ]
#  ]


# filtered_data
#      puts filtered_data.to_json

# output_public_path
#      puts "# #{output_file_genome_path}"

# output_filtered_data.json
#      puts filtered_data.to_json

# graph_mag
#      puts graph_mag.to_json

      # 完全出力時に RGL グラフを DOT 形式で出力したい場合:
      # graph.print_dotted_on
    end
  end
end

#----------------------------------------
# 全件出力する場合に RGL グラフを DOT 形式で出力したいときは以下を有効化
# graph.print_dotted_on
