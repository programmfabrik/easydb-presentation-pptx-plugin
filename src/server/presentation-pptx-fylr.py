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


def fatal(line):
    stderr(line)
    exit(1)


def return_error(realm, msg):
    fatal(json.dumps({
        'type': realm,
        'error': msg
    }, indent=4))


PPTX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PLUGIN_ACTION = 'produce?create_pptx'


def get_json(js, path, expected=False):
    # wrapper for the get_json_value function with exception handling
    try:
        return util.get_json_value(js, path, expected)
    except Exception as e:
        return_error('internal', str(e))


def load_files_from_eas(files, export_id, api_callback_url, api_callback_token):
    try:
        eas_files = []

        for f in files:

            file_id = get_json(f, 'export_file_internal.file_id')
            if file_id is None:
                continue

            f_path = get_json(f, 'path', True)
            eas_url = '%s/export/%s/file/%s' % (api_callback_url,
                                                export_id, f_path)

            resp = requests.get(eas_url,
                                headers={
                                    'token': api_callback_token
                                })

            if resp.status_code == 200:
                util.create_missing_dirs(f_path)
                with open(f_path, 'wb') as outf:
                    outf.write(resp.content)
            else:
                return_error('internal',
                             'could not get file from fylr: status code %s: %s' % (resp.status_code,
                                                                                   resp.text))

            eas_files.append({
                'eas_id': file_id,
                'eas_url': eas_url,
                'path': f_path,
                'body': str(resp.content)
            })

        return eas_files

    except Exception as e:
        fatal(str(e))

    return None


if __name__ == '__main__':

    try:
        # read from %info.json% (needs to be given as the first argument)
        info_json = json.loads(sys.argv[1])

        response = get_json(info_json, 'export', True)

        export_def = get_json(response, 'export', True)
        export_id = get_json(export_def, '_id', True)

        produce_opts = get_json(export_def, 'produce_options', True)

        pptx_filename = 'files/%s' % (util.parse_target_filename(produce_opts))

        plugin_action = get_json(info_json, 'plugin_action')
        if plugin_action == PLUGIN_ACTION:
            api_callback_url = get_json(info_json, 'api_callback.url', True)
            api_callback_token = get_json(
                info_json, 'api_callback.token', True)

            # get files from eas and store locally
            export_files = load_files_from_eas(
                get_json(response, '_files', True),
                export_id,
                api_callback_url,
                api_callback_token)

            # create the pptx file, save as temporary file
            try:
                util.produce_files(
                    produce_opts,
                    '.',
                    export_files,
                    pptx_filename)
            except util.VerboseException as e:
                # fatal(str(e))
                raise e  # XXX

            # write pptx content to stdout
            with open(pptx_filename, 'rb') as pptx_file:
                sys.stdout.write(pptx_file.read())

        else:
            # hide all files that are not exported
            for i in range(len(get_json(response, '_files', True))):
                response['_files'][i]['export_file_internal']['hidden'] = True

            # add the file info and the plugin action for the pptx file to be created
            response['_files'].append({
                'path': pptx_filename,
                'format': PPTX_MIME_TYPE,
                'export_file_internal': {
                    'export_id': export_id,
                    'path': pptx_filename,
                    'format': PPTX_MIME_TYPE,
                    'plugin_action': 'produce?create_pptx'
                }
            })

            # everything ok, set status as done
            response['_state'] = 'done'

            stdout(json.dumps(response, indent=4))

    except Exception as e:
        # fatal(str(e))
        raise e  # XXX
