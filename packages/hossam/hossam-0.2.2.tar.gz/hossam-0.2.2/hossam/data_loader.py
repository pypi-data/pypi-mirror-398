# -*- coding: utf-8 -*-
# -------------------------------------------------------------
"""Data loading utilities for the `hossam` package.

This module provides helpers to load dataset files (CSV/Excel) either
from remote URLs or local paths, and to retrieve dataset metadata from
`metadata.json`. It also prints a small pretty table for Excel metadata
when available.

Attributes:
    BASE_URL: Base URL where remote dataset metadata and files are hosted.

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
    """Load a dataset file (CSV or Excel) into a DataFrame.

    This function supports reading from both local file paths and HTTP/HTTPS
    URLs. For Excel files, if a remote URL is provided, the bytes are fetched
    once and reused for reading both the main sheet and an optional
    ``metadata`` sheet. If the ``metadata`` sheet exists, a pretty table is
    printed for quick inspection.

    Args:
        path: File system path or HTTP/HTTPS URL to the dataset file. Supports
            ``.xlsx`` for Excel and other extensions assumed as CSV.
        index_col: Column(s) to set as the DataFrame index. Accepts the same
            values as ``pandas.read_csv``/``pandas.read_excel``.

    Returns:
        DataFrame: The loaded dataset.

    Raises:
        Exception: If a remote fetch fails (non-200 HTTP status).
        FileNotFoundError: If a local file does not exist.
        ValueError: If the file content is invalid for the selected reader.

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
    """Resolve dataset URL and metadata by key.

    Looks up the dataset entry in ``metadata.json`` either from the remote
    ``BASE_URL`` or a provided local directory. Returns the full path/URL to
    the data file along with its description and index configuration, if any.

    Args:
        key: Dataset key name. Case-insensitive.
        local: Local directory containing ``metadata.json``. If omitted,
            the remote metadata at ``BASE_URL`` is used.

    Returns:
        tuple: ``(path_or_url, desc, index)`` where
            - ``path_or_url`` (str): Full URL or local path to the dataset file.
            - ``desc`` (str or None): Description of the dataset.
            - ``index`` (int, str, list or None): Index column(s) to use.

    Raises:
        FileNotFoundError: If the requested key does not exist or local
            ``metadata.json`` is missing.
        Exception: If fetching remote metadata fails (non-200 HTTP status).

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
    """Load and return the dataset catalog as a DataFrame.

    Reads ``metadata.json`` from the remote ``BASE_URL`` or a local directory
    and returns a curated DataFrame with the columns ``name``, ``chapter``,
    ``desc``, and ``url``. When ``search`` is provided, results are filtered by
    whether the dataset name contains the given substring.

    Args:
        search: Optional substring to filter dataset names (case-insensitive).
        local: Optional local directory containing ``metadata.json``. If not
            provided, remote metadata is used.

    Returns:
        DataFrame: Catalog of available datasets with key details.

    Raises:
        FileNotFoundError: If local ``metadata.json`` is missing.
        Exception: If fetching remote metadata fails (non-200 HTTP status).

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
    """Load a dataset by key and return it as a DataFrame.

    Resolves the dataset file path/URL using ``metadata.json`` and then loads
    the data via ``__get_df``. Prints basic information about the dataset and
    may display an Excel ``metadata`` sheet as a pretty table, if present.

    Args:
        key: Dataset key name to load.
        local: Optional local directory containing ``metadata.json``.

    Returns:
        DataFrame or None: The loaded dataset. Returns ``None`` if an error is
        encountered (errors are printed to stderr-like output).

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
