# encoding: utf-8

import os

from context import EasydbException
from shared import util


def get_json(js, path, expected=False):
    try:
        return util.get_json_value(js, path, expected)
    except Exception as e:
        raise EasydbException('internal', str(e))


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger('presentation-pptx')
    logger.debug('PPTX started')

    easydb_context.register_callback('export_produce', {
        'callback': 'produce_files',
    })


def produce_files(easydb_context, parameters, protocol=None):
    global pack_dir

    exp = easydb_context.get_exporter()
    produce_opts = get_json(exp.getExport(), 'export.produce_options', True)
    logger = easydb_context.get_logger('export.pptx')

    if 'pptx' not in produce_opts:
        return

    logger.debug('parameters: %s' % parameters)

    logger.debug('exp: %s' % exp)
    if not exp:
        logger.error('could not get exporter object')
        return

    for plugin in easydb_context.get_plugins()['plugins']:
        if plugin['name'] == 'presentation-pptx':
            break

    # produce slides
    basepath = os.path.abspath(os.path.dirname(__file__))

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

        logger.debug('adding slide[%d], type: %s | %s | %s' % (
            slide_id, stype, repr(sl_info), repr(slide)))
        ppt_slide = prs.slides.add_slide(sl['layout'])

        title_key = get_json(sl_info, 'title')
        subtitle_key = get_json(sl_info, 'subtitle')

        data_title = get_json(slide, 'data.title')
        data_info = get_json(slide, 'data.info')

        if stype == 'start':
            if not 'data' in slide:
                logger.warn(
                    'key data missing in slide[%d] in produce_opts' % slide_id)
                continue

            if title_key is not None and data_title is not None:
                ppt_slide.placeholders[title_key].text = data_title
            if subtitle_key is not None and data_info is not None:
                ppt_slide.placeholders[subtitle_key].text = data_info

        elif stype == 'bullets':
            if not 'data' in slide:
                logger.warn(
                    'key data missing in slide[%d] in produce_opts' % slide_id)
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
                logger.warn(
                    'key center missing in slide[%d] in produce_opts' % slide_id)
                continue

            if not 'global_object_id' in slide['center']:
                logger.warn(
                    'key global_object_id missing in slide[%d].center in produce_opts' % slide_id)
                continue

            picture_bottom_line = util.insert_picture(exp.getFilesPath(),
                                                      exp.getFiles(),
                                                      ppt_slide.placeholders[sl_info['picture']],
                                                      ppt_slide.shapes,
                                                      get_json(
                                                          slide, 'center.asset_id', True),
                                                      get_json(
                                                          slide, 'center.asset_url'),
                                                      logger)

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
                logger.warn(
                    'keys left and right missing in slide[%d] in produce_opts' % slide_id)
                continue

            if 'left' in slide:
                if 'global_object_id' in slide['left'] and 'picture_left' in sl_info:
                    picture_bottom_lines.append(
                        util.insert_picture(exp.getFilesPath(),
                                            exp.getFiles(),
                                            ppt_slide.placeholders[sl_info['picture_left']],
                                            ppt_slide.shapes,
                                            get_json(
                                                slide, 'left.asset_id', True),
                                            get_json(slide, 'left.asset_url'),
                                            logger))

            if 'right' in slide:
                if 'global_object_id' in slide['right'] and 'picture_right' in sl_info:
                    picture_bottom_lines.append(
                        util.insert_picture(exp.getFilesPath(),
                                            exp.getFiles(),
                                            ppt_slide.placeholders[sl_info['picture_right']],
                                            ppt_slide.shapes,
                                            get_json(
                                                slide, 'right.asset_id', True),
                                            get_json(slide, 'right.asset_url'),
                                            logger))

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

        else:
            logger.warn(
                'unknown type %s in slide[%d] in produce_opts' % (stype, slide_id))

    pack_dir = easydb_context.get_temp_dir()
    pptx_filename = '%s/produce.pptx' % pack_dir
    target_filename = util.parse_target_filename(produce_opts)

    prs.save(pptx_filename)
    exp.addFile(pptx_filename, target_filename)
