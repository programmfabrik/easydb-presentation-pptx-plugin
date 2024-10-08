# encoding: utf-8


import requests
import os


def get_json_value(js: dict[str], path: str, expected: bool = False) -> any:
    current = js
    path_parts = path.split('.')
    for path_part in path_parts:
        if not isinstance(current, dict) or path_part not in current:
            if expected:
                raise Exception(f'expected: {path}')
            else:
                return None
        current = current[path_part]
    return current


def parse_target_filename(produce_opts: dict[str]) -> str:
    return f"{get_json_value(produce_opts, 'presentation.filename', True)}.pptx"


def download_export_file(url: str, filename: str) -> None:
    resp = requests.get(url)
    if resp.status_code == 200:
        create_missing_dirs(filename)
        with open(os.path.abspath(filename), 'wb') as outf:
            outf.write(resp.content)
    else:
        raise Exception(
            f'could not get file from fylr: status code {resp.status_code}: {resp.text}'
        )


def create_missing_dirs(f_path: str) -> None:
    base_dir = '/'.join(f_path.split('/')[:-1])
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
