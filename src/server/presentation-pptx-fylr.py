# encoding: utf-8

import os
import sys
import json
import requests

from shared import util


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


def produce_files(produce_opts, export_files, basepath, pptx_filename):

    standard_format = util.get_standard_format()
    show_standard = util.parse_show_standard(produce_opts)

    prs = util.new_presentation(template_path='%s/%s' % (basepath,
                                                         get_json(produce_opts, 'pptx_form.template.name', True)))

    slide_layouts = util.parse_slide_layouts(prs, produce_opts, show_standard)
    data_by_gid = get_json(produce_opts, 'presentation.data_by_gid', True)

    slide_id = -1
    for slide in get_json(produce_opts, 'presentation.slides', True):
        slide_id += 1

        stype = slide['type']

        sl = slide_layouts[stype]
        sl_info = sl['info']

        ppt_slide = prs.slides.add_slide(sl['layout'])

        title_key = get_json(sl_info, 'title')
        subtitle_key = get_json(sl_info, 'subtitle')

        data_title = get_json(slide, 'data.title')
        data_info = get_json(slide, 'data.info')

        if stype == 'start':
            if not 'data' in slide:
                continue

            if title_key is not None and data_title is not None:
                ppt_slide.placeholders[title_key].text = data_title
            if subtitle_key is not None and data_info is not None:
                ppt_slide.placeholders[subtitle_key].text = data_info

        elif stype == 'bullets':
            if not 'data' in slide:
                continue

            if title_key is not None and data_title is not None:
                ppt_slide.placeholders[title_key].text = data_title

            text_frame = ppt_slide.placeholders[sl_info['bullets']].text_frame
            text_frame.clear()  # remove any existing paragraphs, leaving one empty one

            rows = slide['data']['info'].split('\n')

            p = text_frame.paragraphs[0]
            p.text = rows[0]

            for row in rows[1:]:
                p = text_frame.add_paragraph()
                p.text = row

        elif stype == 'one':
            if not 'center' in slide:
                continue

            if not 'global_object_id' in slide['center']:
                continue

            picture_bottom_line = util.insert_picture('.', export_files,
                                                      ppt_slide.placeholders[sl_info['picture']],
                                                      ppt_slide.shapes,
                                                      get_json(
                                                          slide, 'center.asset_id', True),
                                                      get_json(slide, 'center.asset_url'))

            if 'text' in sl_info:
                util.insert_info(ppt_slide.placeholders[sl_info['text']],
                                 ppt_slide.shapes,
                                 slide['center']['global_object_id'],
                                 data_by_gid,
                                 show_standard,
                                 standard_format,
                                 picture_bottom_line)

        elif stype == 'duo':
            picture_bottom_lines = []

            if not 'left' in slide and not 'right' in slide:
                continue

            if 'left' in slide:
                if 'global_object_id' in slide['left'] and 'picture_left' in sl_info:
                    picture_bottom_lines.append(
                        util.insert_picture('.', export_files,
                                            export_files,
                                            ppt_slide.placeholders[sl_info['picture_left']],
                                            ppt_slide.shapes,
                                            get_json(
                                                slide, 'left.asset_id', True),
                                            get_json(slide, 'left.asset_url')))

            if 'right' in slide:
                if 'global_object_id' in slide['right'] and 'picture_right' in sl_info:
                    picture_bottom_lines.append(
                        util.insert_picture('.', export_files,
                                            export_files,
                                            ppt_slide.placeholders[sl_info['picture_right']],
                                            ppt_slide.shapes,
                                            get_json(
                                                slide, 'right.asset_id', True),
                                            get_json(slide, 'right.asset_url')))

            lowest_picture_bottom_line = None
            if len(picture_bottom_lines) > 0:
                lowest_picture_bottom_line = max(picture_bottom_lines)

            if 'left' in slide:
                if 'global_object_id' in slide['left'] and 'text_left' in sl_info:
                    util.insert_info(ppt_slide.placeholders[sl_info['text_left']],
                                     ppt_slide.shapes,
                                     get_json(
                                         slide, 'left.global_object_id', True),
                                     data_by_gid,
                                     show_standard,
                                     standard_format,
                                     lowest_picture_bottom_line)

            if 'right' in slide:
                if 'global_object_id' in slide['right'] and 'text_right' in sl_info:
                    util.insert_info(ppt_slide.placeholders[sl_info['text_right']],
                                     ppt_slide.shapes,
                                     get_json(
                        slide, 'right.global_object_id', True),
                        data_by_gid,
                        show_standard,
                        standard_format,
                        lowest_picture_bottom_line)

    util.create_missing_dirs(pptx_filename)
    prs.save(pptx_filename)


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
                'path': f_path
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

        basepath = os.path.abspath(os.path.dirname(__file__))
        pptx_filename = 'files/%s' % (util.parse_target_filename(produce_opts))

        plugin_action = get_json(info_json, 'plugin_action')
        if plugin_action == PLUGIN_ACTION:
            api_callback_url = get_json(info_json, 'api_callback.url', True)
            api_callback_token = get_json(
                info_json, 'api_callback.token', True)

            # get files from eas and store locally
            export_files = load_files_from_eas(get_json(response, '_files', True),
                                               export_id,
                                               api_callback_url,
                                               api_callback_token)

            # create the pptx file, save as temporary file
            produce_files(produce_opts,
                          export_files,
                          basepath,
                          pptx_filename)

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

            # increment the export version
            response['export']['_version'] = int(
                get_json(export_def, '_version', True))+1

            stdout(json.dumps(response, indent=4))

    except Exception as e:
        fatal(str(e))
