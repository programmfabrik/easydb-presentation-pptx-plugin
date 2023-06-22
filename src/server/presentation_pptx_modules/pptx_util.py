# encoding: utf-8


import requests
import os


def get_json_value(js, path, expected=False):
    current = js
    path_parts = path.split('.')
    for path_part in path_parts:
        if not isinstance(current, dict) or path_part not in current:
            if expected:
                raise Exception('expected: {0}'.format(path))
            else:
                return None
        current = current[path_part]
    return current


def parse_target_filename(produce_opts):
    return '{0}.pptx'.format(get_json_value(produce_opts, 'presentation.filename', True))


def download_export_file(url, filename):
    resp = requests.get(url)
    if resp.status_code == 200:
        create_missing_dirs(filename)
        with open(os.path.abspath(filename), 'wb') as outf:
            outf.write(resp.content)
    else:
        raise Exception('could not get file from fylr: status code {0}: {1}'.format(resp.status_code, resp.text))


def create_missing_dirs(f_path):
    base_dir = '/'.join(f_path.split('/')[:-1])
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
