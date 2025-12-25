# -*- coding: utf-8 -*-
# -------------------------------------------------------------
"""데이터 로딩 유틸리티.

이 모듈은 원격 URL 또는 로컬 경로에서 CSV/Excel 데이터셋 파일을 로드하고,
`metadata.json`에서 데이터셋 메타데이터를 조회하는 기능을 제공합니다.
또한 Excel 메타데이터 시트가 있을 때 보기 좋은 테이블로 출력합니다.

속성:
    BASE_URL: 원격 데이터셋 메타데이터 및 파일이 호스팅되는 기본 URL.

"""
import requests
import json
from os.path import join, exists
from io import BytesIO
from pandas import DataFrame, read_csv, read_excel

from .util import my_pretty_table

BASE_URL = "https://data.hossam.kr"

# -------------------------------------------------------------

def __get_df(path: str, index_col=None) -> DataFrame:
    """데이터셋 파일(CSV 또는 Excel)을 DataFrame으로 로드합니다.

    로컬 파일 경로와 HTTP/HTTPS URL 모두에서 읽기를 지원합니다.
    Excel 파일의 경우 원격 URL이 제공되면 바이트를 한 번 가져와 메인 시트와
    선택적 ``metadata`` 시트 모두를 읽을 때 재사용합니다.
    ``metadata`` 시트가 존재하면 보기 좋은 테이블로 출력합니다.

    인자:
        path: 데이터셋 파일의 파일 시스템 경로 또는 HTTP/HTTPS URL.
            ``.xlsx``는 Excel로, 다른 확장자는 CSV로 처리합니다.
        index_col: DataFrame 인덱스로 설정할 열. ``pandas.read_csv``/
            ``pandas.read_excel``과 같은 값들을 수용합니다.

    반환:
        DataFrame: 로드된 데이터셋.

    예외:
        Exception: 원격 조회 실패 (non-200 HTTP 상태).
        FileNotFoundError: 로컬 파일이 존재하지 않음.
        ValueError: 파일 콘텐츠가 선택한 리더에 유효하지 않음.

    """
    p = path.rfind(".")
    exec = path[p+1:].lower()

    if exec == 'xlsx':
        # If path is a remote URL, fetch the file once and reuse the bytes
        if path.lower().startswith(('http://', 'https://')):
            path = path.replace("\\", "/")
            with requests.Session() as session:
                r = session.get(path)

                if r.status_code != 200:
                    raise Exception(f"HTTP {r.status_code} Error - {r.reason} > {path}")

                data_bytes = r.content

            # Use separate BytesIO objects for each read to avoid pointer/stream issues
            df = read_excel(BytesIO(data_bytes), index_col=index_col)

            try:
                info = read_excel(BytesIO(data_bytes), sheet_name='metadata', index_col=0)
                #print("\033[94m[metadata]\033[0m")
                print()
                my_pretty_table(info)
                print()
            except Exception:
                print(f"\033[91m[!] Cannot read metadata\033[0m")
        else:
            df = read_excel(path, index_col=index_col)

            try:
                info = read_excel(path, sheet_name='metadata', index_col=0)
                #print("\033[94m[metadata]\033[0m")
                print()
                my_pretty_table(info)
                print()
            except:
                print(f"\033[91m[!] Cannot read metadata\033[0m")
    else:
        df = read_csv(path, index_col=index_col)

    return df

# -------------------------------------------------------------

def __get_data_url(key: str, local: str = None) -> str:
    """키를 기준으로 데이터셋 URL과 메타데이터를 조회합니다.

    원격 ``BASE_URL`` 또는 제공된 로컬 디렉토리에서 ``metadata.json``의
    데이터셋 항목을 찾습니다. 데이터 파일의 전체 경로/URL과 함께
    설명 및 인덱스 설정(있는 경우)을 반환합니다.

    인자:
        key: 데이터셋 키 이름. 대소문자를 구분하지 않습니다.
        local: ``metadata.json``을 포함하는 로컬 디렉토리. 생략하면
            ``BASE_URL``의 원격 메타데이터를 사용합니다.

    반환:
        tuple: ``(path_or_url, desc, index)`` 형태로
            - ``path_or_url`` (str): 데이터셋 파일의 전체 URL 또는 로컬 경로.
            - ``desc`` (str 또는 None): 데이터셋 설명.
            - ``index`` (int, str, list 또는 None): 사용할 인덱스 열.

    예외:
        FileNotFoundError: 요청한 키가 존재하지 않거나 로컬
            ``metadata.json``이 누락됨.
        Exception: 원격 메타데이터 조회 실패 (non-200 HTTP 상태).

    """
    global BASE_URL

    path = None

    if not local:
        data_path = join(BASE_URL, "metadata.json").replace("\\", "/")

        with requests.Session() as session:
            r = session.get(data_path)

            if r.status_code != 200:
                raise Exception("[%d Error] %s" % (r.status_code, r.reason))

        my_dict = r.json()
        info = my_dict.get(key.lower())

        if not info:
            raise FileNotFoundError("%s는 존재하지 않는 데이터에 대한 요청입니다." % key)

        path = join(BASE_URL, info['url'])
    else:
        data_path = join(local, "metadata.json")

        if not exists(data_path):
            raise FileNotFoundError("존재하지 않는 데이터에 대한 요청입니다.")

        with open(data_path, "r", encoding="utf-8") as f:
            my_dict = json.loads(f.read())

        info = my_dict.get(key.lower())
        path = join(local, info['url'])

    return path, info.get('desc'), info.get('index')

# -------------------------------------------------------------

def load_info(search: str = None, local: str = None):
    """데이터셋 카탈로그를 DataFrame으로 로드하고 반환합니다.

    원격 ``BASE_URL`` 또는 로컬 디렉토리에서 ``metadata.json``을 읽고,
    ``name``, ``chapter``, ``desc``, ``url`` 열을 가진 큐레이션된
    DataFrame을 반환합니다. ``search``가 제공되면 결과를 데이터셋 이름이
    주어진 부분 문자열을 포함하는지 여부로 필터링합니다.

    인자:
        search: 데이터셋 이름을 필터링할 선택적 부분 문자열 (대소문자 미구분).
        local: ``metadata.json``을 포함하는 선택적 로컬 디렉토리.
            제공되지 않으면 원격 메타데이터를 사용합니다.

    반환:
        DataFrame: 주요 세부사항이 포함된 사용 가능한 데이터셋 카탈로그.

    예외:
        FileNotFoundError: 로컬 ``metadata.json``이 누락됨.
        Exception: 원격 메타데이터 조회 실패 (non-200 HTTP 상태).

    """
    global BASE_URL

    path = None

    if not local:
        data_path = join(BASE_URL, "metadata.json").replace("\\", "/")

        with requests.Session() as session:
            r = session.get(data_path)

            if r.status_code != 200:
                raise Exception("[%d Error] %s ::: %s" % (r.status_code, r.reason, data_path))

        my_dict = r.json()
    else:
        data_path = join(local, "metadata.json")

        if not exists(data_path):
            raise FileNotFoundError("존재하지 않는 데이터에 대한 요청입니다.")

        with open(data_path, "r", encoding="utf-8") as f:
            my_dict = json.loads(f.read())

    my_data = []
    for key in my_dict:
        if 'index' in my_dict[key]:
            del my_dict[key]['index']

        my_dict[key]['url'] = "%s/%s" % (BASE_URL, my_dict[key]['url'])
        my_dict[key]['name'] = key

        if 'chapter' in my_dict[key]:
            my_dict[key]['chapter'] = ", ".join(my_dict[key]['chapter'])
        else:
            my_dict[key]['chapter'] = '공통'

        my_data.append(my_dict[key])

    my_df = DataFrame(my_data)
    my_df2 = my_df.reindex(columns=['name', 'chapter', 'desc', 'url'])

    if search:
        my_df2 = my_df2[my_df2['name'].str.contains(search.lower())]

    return my_df2

# -------------------------------------------------------------

def load_data(key: str, local: str = None):
    """키를 기준으로 데이터셋을 로드하고 DataFrame으로 반환합니다.

    ``metadata.json``을 사용하여 데이터셋 파일 경로/URL을 찾고,
    ``__get_df``를 통해 데이터를 로드합니다. 데이터셋에 대한 기본 정보를
    출력하며, Excel ``metadata`` 시트가 있으면 보기 좋은 테이블로
    표시할 수 있습니다.

    인자:
        key: 로드할 데이터셋 키 이름.
        local: ``metadata.json``을 포함하는 선택적 로컬 디렉토리.

    반환:
        DataFrame 또는 None: 로드된 데이터셋. 오류 발생 시 ``None``을
        반환합니다 (오류는 표준 출력처럼 출력됨).

    """
    index = None
    try:
        url, desc, index = __get_data_url(key, local=local)
    except Exception as e:
        try:
            print(f"\033[91m{str(e)}\033[0m")
        except Exception:
            print(e)
        return

    print("\033[94m[data]\033[0m", url.replace("\\", "/"))
    print("\033[94m[desc]\033[0m", desc)

    df = None

    try:
        df = __get_df(url, index_col=index)
    except Exception as e:
        try:
            print(f"\033[91m{str(e)}\033[0m")
        except Exception:
            print(e)
        return


    return df

if __name__ == "__main__":
    print(load_info())
    df = load_data("boston")
    my_pretty_table(df)
