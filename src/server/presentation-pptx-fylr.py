# encoding: utf-8

import sys
import json

import util
from fylr_lib_plugin_python3 import util as fylr_util


PPTX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PLUGIN_ACTION = 'produce?create_pptx'


def load_files_from_eas(files, export_id, api_callback_url, api_callback_token):

    eas_files = []

    if not isinstance(files, list):
        # in case the objects that are exported have no asset fields, there is nothing to be done here
        return eas_files

    for f in files:
        try:

            file_id = fylr_util.get_json_value(f, 'export_file_internal.file_id')
            if not isinstance(file_id, int):
                continue

            f_path = fylr_util.get_json_value(f, 'path', True)
            util.download_export_file(
                '{0}/api/v1/export/{1}/file/{2}?access_token={3}'.format(
                    api_callback_url,
                    export_id,
                    f_path,
                    api_callback_token),
                f_path
            )
            eas_files.append({
                'eas_id': file_id,
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

        export_def = fylr_util.get_json_value(info_json, 'export.export', True)
        produce_opts = fylr_util.get_json_value(export_def, 'produce_options', True)

        pptx_filename = 'files/{0}'.format(util.parse_target_filename(produce_opts))

        plugin_action = fylr_util.get_json_value(info_json, 'plugin_action')
        if plugin_action == PLUGIN_ACTION:

            # fylr export is done on the fly, so request the exported images and save them in a temporary folder
            export_files = load_files_from_eas(
                files=fylr_util.get_json_value(info_json, 'export._files', True),
                export_id=fylr_util.get_json_value(export_def, '_id', True),
                api_callback_url=fylr_util.get_json_value(info_json, 'api_callback.url', True),
                api_callback_token=fylr_util.get_json_value(info_json, 'api_callback.token', True),
            )

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

            response = fylr_util.get_json_value(info_json, 'export', True)

            if fylr_util.get_json_value(response, 'export.search') is None:
                response['export']['search'] = {}

            # hide all files that are not exported
            if not '_files' in response:
                response['_files'] = []
            for i in range(len(response['_files'])):
                response['_files'][i]['export_file_internal']['hidden'] = True

            # add the file info and the plugin action for the pptx file to be created
            response['_files'].append({
                'path': pptx_filename,
                'format': PPTX_MIME_TYPE,
                'export_file_internal': {
                    'path': pptx_filename,
                    'content_type': PPTX_MIME_TYPE,
                    'plugin_action': PLUGIN_ACTION,
                    'info': {},
                }
            })
            response['_plugin_log'] = [
                'prepared pptx file: ' + pptx_filename
            ]
            del response['_log']
            response['_state'] = 'done'

            # everything ok, set status as done
            fylr_util.return_response(response)

    except Exception as e:
        fylr_util.return_error_response(str(e))
