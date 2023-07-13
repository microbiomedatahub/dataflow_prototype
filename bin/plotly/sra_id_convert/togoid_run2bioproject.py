# encoding: utf-8
from typing import List
import urllib.request
import urllib.parse
import json

def run_bioproject(run: list) -> List[list]:
    """
    TogoID APIを利用して、Run IDからBioProject IDを取得する
    TogoID APIのlimitを5000に設定しているので、一度に5000件までしか取得できないことに留意すること
    :param run: runのlist
    :return: run,bioprojectのID list of list
    """
    ids = ','.join(run)
    url = 'https://api.togoid.dbcls.jp/convert?ids={ids}&route=sra_run%2Cbioproject&report=pair&format=json&limit=5000&offset=0'.format(
        ids=ids)
    res = urllib.request.urlopen(url)
    json_data = res.read().decode('utf-8')
    run_bp = json.loads(json_data)
    return run_bp['results']


def convert_nested_bioproject_list(run_bioprojects:list) -> dict:
    """_summary_
    [[run, bioproject],,]形式のrun-bioprojectデータを、bioprojectキーにしたdictに変換する
    :return: {bioproject:[run, run,,,],,, }
    """
    bioproject_dict = {}
    for run_bioproject in run_bioprojects:
        run = run_bioproject[0]
        bioproject = run_bioproject[1]
        # Todo: defaultdictを使う
        if bioproject in bioproject_dict:
            bioproject_dict[bioproject].append(run)
        else:
            bioproject_dict[bioproject] = [run]
    return bioproject_dict


if __name__ == "__main__":
    run_bioproject()