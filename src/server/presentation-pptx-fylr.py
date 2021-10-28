# encoding: utf-8

import os
import sys
import json
import requests

import util


def stdout(line):
    sys.stdout.write(line)
    sys.stdout.write('\n')


def stderr(line):
    sys.stderr.write(line)
    sys.stderr.write('\n')


def return_response(response, status='done'):
    response['_state'] = status
    stdout(json.dumps(response))
    exit(0)


def return_error_response(error):
    stderr(error)
    exit(1)


PPTX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PLUGIN_ACTION = 'produce?create_pptx'


def load_files_from_eas(files, export_id, api_callback_url, api_callback_token):
    eas_files = []

    for f in files:

        try:

            file_id = util.get_json_value(f, 'export_file_internal.file_id')
            if file_id is None:
                continue

            f_path = util.get_json_value(f, 'path', True)
            eas_url = '%s/api/v1/export/%s/file/%s' % (
                api_callback_url, export_id, f_path)

            resp = requests.get(eas_url,
                                headers={
                                    'x-easydb-token': api_callback_token
                                })

            if resp.status_code == 200:
                util.create_missing_dirs(f_path)
                with open(f_path, 'wb') as outf:
                    outf.write(resp.content)
            else:
                raise util.VerboseException('could not get file from fylr: status code %s: %s' %
                                            (resp.status_code, resp.text))

            eas_files.append({
                'eas_id': file_id,
                'eas_url': eas_url,
                'path': f_path
            })

        except Exception as e:
            eas_files.append({
                'error': str(e)
            })

    return eas_files


if __name__ == '__main__':

    try:
        # read from %info.json% (needs to be given as the first argument)
        info_json = json.loads(sys.argv[1])
        response = util.get_json_value(info_json, 'export', True)

        export_def = util.get_json_value(response, 'export', True)
        export_id = util.get_json_value(export_def, '_id', True)

        produce_opts = util.get_json_value(export_def, 'produce_options', True)

        pptx_filename = 'files/%s' % (util.parse_target_filename(produce_opts))

        plugin_action = util.get_json_value(info_json, 'plugin_action')
        if plugin_action == PLUGIN_ACTION:
            api_callback_url = util.get_json_value(
                info_json, 'api_callback.url', True)
            api_callback_token = util.get_json_value(
                info_json, 'api_callback.token', True)

            # get files from eas and store locally
            export_files = load_files_from_eas(
                util.get_json_value(response, '_files', True),
                export_id,
                api_callback_url,
                api_callback_token)

            # create the pptx file, save as temporary file
            util.produce_files(
                produce_opts,
                '.',
                export_files,
                pptx_filename)

            # write pptx content to stdout
            with open(pptx_filename, 'rb') as pptx_file:
                sys.stdout.buffer.write(pptx_file.read())
                exit(0)

        else:
            # hide all files that are not exported
            for i in range(len(util.get_json_value(response, '_files', True))):
                response['_files'][i]['export_file_internal']['hidden'] = True

            # add the file info and the plugin action for the pptx file to be created
            response['_files'].append({
                'path': pptx_filename,
                'format': PPTX_MIME_TYPE,
                'export_file_internal': {
                    'export_id': export_id,
                    'path': pptx_filename,
                    'format': PPTX_MIME_TYPE,
                    'plugin_action': PLUGIN_ACTION
                }
            })

            # everything ok, set status as done
            return_response(response)

    except util.VerboseException as e:
        return_error_response(e.getMessage())
    except Exception as e:
        return_error_response(str(e))
