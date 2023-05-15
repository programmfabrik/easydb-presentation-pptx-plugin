# encoding: utf-8

import sys
import json
from urllib import response

import util

from fylr_lib_plugin_python3 import util as fylr_util


PPTX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PLUGIN_ACTION = 'produce?create_pptx'


if __name__ == '__main__':

    try:
        # read from %info.json% (needs to be given as the first argument)
        info_json = json.loads(sys.argv[1])

        export_def = fylr_util.get_json_value(info_json, 'export.export', True)
        export_id = fylr_util.get_json_value(export_def, '_id', True)

        produce_opts = fylr_util.get_json_value(
            export_def, 'produce_options', True)

        pptx_filename = 'files/%s' % (util.parse_target_filename(produce_opts))

        plugin_action = fylr_util.get_json_value(info_json, 'plugin_action')
        if plugin_action == PLUGIN_ACTION:
            api_callback_url = fylr_util.get_json_value(
                info_json, 'api_callback.url', True)
            api_callback_token = fylr_util.get_json_value(
                info_json, 'api_callback.token', True)

            # get files from eas and store locally
            export_files = util.load_files_from_eas(
                fylr_util.get_json_value(info_json, 'export._files'),
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
                'built pptx file: ' + pptx_filename
            ]
            response['_state'] = 'done'

            # everything ok, set status as done
            fylr_util.return_response(response)

    except util.VerboseException as e:
        fylr_util.return_error_response(e.getMessage())
    except Exception as e:
        fylr_util.return_error_response(str(e))
