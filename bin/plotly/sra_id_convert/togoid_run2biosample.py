# encoding: utf-8
import urllib.request
import urllib.parse
import json

# togoidを利用しf(Run): BioSampleの変換を行う
# plotlyのstacked chart用の変換であるため、同一のIDが同じプロジェクトに含まれるのは都合が悪いため、IDが重なる場合はsuffixを付与する


def run_biosample(run: list) -> dict:
    """
    TogoID APIを利用して、Run IDからBioSample IDを取得する
    :param run:
    :return: BioSample ID
    """
    ids = ','.join(run)
    url = 'https://api.togoid.dbcls.jp/convert?ids={ids}&route=sra_run%2Cbiosample&report=pair&format=json&limit=1000&offset=0'.format(ids=ids)
    res = urllib.request.urlopen(url)
    json_data = res.read().decode('utf-8')
    run_bs = json.loads(json_data)
    # APIのレスポンスよりrun_bs["results"]で、[[run,biosample], [run, biosample], ...]の形式としてBioSample IDがフルセット分取得できる
    # add_sufixを呼び出し、同一のBioSample IDを含む場合、suffixを付与する
    run_bs_dict = add_sufix(run_bs['results'])
    # Todo: データ形式をDFのカラム名様最適化する
    return dict(run_bs_dict)


def add_sufix(run_bs: list) -> list:
    """
    同一のBioSample IDを含む場合、suffixを付与する
    add suffix to BioSample ID if it is duplicated
    :parama run_bs: (run,biosample)のlist of list
    :return: BioSampleが複数ある場合suffixを追加した、list of list
    """
    # defaultdictで{biosample: count}を作成し、suffixに利用する
    bs_list = [x[1] for x in run_bs]
    # bs_set: ユニークなbiosampleのセット
    bs_set = set(bs_list)
    # bs_dict = {x: bs_list.count(x) for x in bs_set}
    bs_dict = {}
    bs_count = {}
    for bs in bs_set:
        # それぞれのbiosampleの出現回数
        bs_dict[bs] = bs_list.count(bs)
        # bs_countはrun:biosampleの組み合わせを参照されるごとに徐算する
        bs_count[bs] = bs_dict[bs]
    for i in range(len(run_bs)):
        bs = run_bs[i][1]
        if bs_dict[bs] > 1:
            run_bs[i] = (run_bs[i][0], run_bs[i][1] + '_' + str(bs_count[bs]))
            bs_count[bs] -= 1
    return run_bs


if __name__ == "__main__":
    d = run_biosample(['SRR2198979', 'SRR2198982', 'SRR2199220', 'SRR2223198', 'SRR2223207', 'SRR2223229', 'SRR2223242', 'SRR2223418',
                       'SRR2223495', 'SRR2223515','SRR2226375'])
