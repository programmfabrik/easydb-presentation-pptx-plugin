# encoding: utf-8

from pptx import Presentation
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN

from PIL import Image

import hashlib
import urllib
import os
import json


class VerboseException(Exception):
    def __init__(self, msg):
        Exception()
        self.msg = msg

    def __str__(self):
        return self.msg


def get_json_value(js, path, expected=False):
    current = js
    path_parts = path.split('.')
    for path_part in path_parts:
        if not isinstance(current, dict) or path_part not in current:
            if expected:
                raise Exception('expected: {0}'.format(path_part))
            else:
                return None
        current = current[path_part]
    return current


def get_template_basepath():
    return '%s/../templates' % os.path.abspath(os.path.dirname(__file__))


def pixels_to_emu(px, dpi=72):
    return float(px * (914400 / dpi))


def new_presentation(template_path):
    return Presentation(template_path)


def get_standard_format():
    return {
        '1': {
            'size': 26,
            'bold': True
        },
        '2': {
            'size': 19,
            'bold': False
        },
        '3': {
            'size': 16,
            'bold': False
        }
    }


def parse_target_filename(produce_opts):
    return '%s.pptx' % produce_opts['presentation']['filename']


def parse_show_standard(produce_opts):
    if not 'show_standard' in produce_opts['presentation']['settings']:
        return []
    return [s.strip() for s in produce_opts['presentation']['settings']['show_standard'].split(' ')]


def parse_slide_layouts(prs, produce_opts, show_standard):
    slide_layouts = {}

    for slide in produce_opts['pptx_form']['template']['slides']:
        if len(show_standard) > 0:
            if 'show_info' in slide and slide['show_info'] == True:
                slide_layouts[slide['type']] = {
                    'layout': prs.slide_layouts[slide['slide_idx']],
                    'info': slide,
                }
        else:
            if 'show_info' not in slide or slide['show_info'] == False:
                slide_layouts[slide['type']] = {
                    'layout': prs.slide_layouts[slide['slide_idx']],
                    'info': slide,
                }

    return slide_layouts


def produce_files(produce_opts, files_path, export_files, pptx_filename):

    standard_format = get_standard_format()
    show_standard = parse_show_standard(produce_opts)

    prs = new_presentation(template_path='%s/%s' % (
        get_template_basepath(),
        get_json_value(produce_opts, 'pptx_form.template.name', True)))

    slide_layouts = parse_slide_layouts(prs, produce_opts, show_standard)
    data_by_gid = get_json_value(
        produce_opts, 'presentation.data_by_gid', True)

    slide_id = -1
    for slide in get_json_value(produce_opts, 'presentation.slides', True):
        slide_id += 1

        stype = slide['type']

        sl = slide_layouts[stype]
        sl_info = sl['info']

        ppt_slide = prs.slides.add_slide(sl['layout'])

        title_key = get_json_value(sl_info, 'title')
        subtitle_key = get_json_value(sl_info, 'subtitle')

        data_title = get_json_value(slide, 'data.title')
        data_info = get_json_value(slide, 'data.info')

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

            picture_bottom_line = insert_picture(
                files_path,
                export_files,
                ppt_slide.placeholders[sl_info['picture']],
                ppt_slide.shapes,
                get_json_value(
                    slide, 'center.asset_id', True),
                get_json_value(slide, 'center.asset_url'))

            if 'text' in sl_info:
                insert_info(
                    ppt_slide.placeholders[sl_info['text']],
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
                        insert_picture(
                            files_path,
                            export_files,
                            ppt_slide.placeholders[sl_info['picture_left']],
                            ppt_slide.shapes,
                            get_json_value(
                                slide, 'left.asset_id', True),
                            get_json_value(slide, 'left.asset_url')))

            if 'right' in slide:
                if 'global_object_id' in slide['right'] and 'picture_right' in sl_info:
                    picture_bottom_lines.append(
                        insert_picture(
                            files_path,
                            export_files,
                            ppt_slide.placeholders[sl_info['picture_right']],
                            ppt_slide.shapes,
                            get_json_value(
                                slide, 'right.asset_id', True),
                            get_json_value(slide, 'right.asset_url')))

            lowest_picture_bottom_line = None
            if len(picture_bottom_lines) > 0:
                lowest_picture_bottom_line = max(picture_bottom_lines)

            if 'left' in slide:
                if 'global_object_id' in slide['left'] and 'text_left' in sl_info:
                    insert_info(
                        ppt_slide.placeholders[sl_info['text_left']],
                        ppt_slide.shapes,
                        get_json_value(
                            slide, 'left.global_object_id', True),
                        data_by_gid,
                        show_standard,
                        standard_format,
                        lowest_picture_bottom_line)

            if 'right' in slide:
                if 'global_object_id' in slide['right'] and 'text_right' in sl_info:
                    insert_info(
                        ppt_slide.placeholders[sl_info['text_right']],
                        ppt_slide.shapes,
                        get_json_value(
                            slide, 'right.global_object_id', True),
                        data_by_gid,
                        show_standard,
                        standard_format,
                        lowest_picture_bottom_line)

    create_missing_dirs(pptx_filename)
    prs.save(pptx_filename)


def insert_info(placeholder, shapes, gid, data_by_gid, show_standard, standard_format, picture_bottom_line):
    if gid not in data_by_gid:
        return

    top = placeholder.top

    if picture_bottom_line is not None:
        top = min([picture_bottom_line + pixels_to_emu(10), top])

    text_box = shapes.add_textbox(
        placeholder.left, top, placeholder.width, placeholder.height)
    text_box.text_frame.word_wrap = True

    first_standard_value = True
    for s in show_standard:
        if not s in standard_format:
            continue

        if s in data_by_gid[gid]['standard_info']:
            _s = data_by_gid[gid]['standard_info'][s].strip()
            if len(_s) < 1:
                continue

            if first_standard_value:
                first_standard_value = False
                p = text_box.text_frame.paragraphs[0]
            else:
                p = text_box.text_frame.add_paragraph()

            p.text = _s
            p.alignment = PP_ALIGN.CENTER
            p.font.name = 'Helvetica'
            p.font.size = Pt(standard_format[s]['size'])
            p.font.bold = standard_format[s]['bold']

    # remove the original placeholder since it is not needed
    placeholder._element.getparent().remove(placeholder._element)


def insert_picture(exp_files_path, exp_files, placeholder, shapes, eas_id, asset_url):

    picture_bottom_line = None

    if eas_id is None and asset_url is None:
        raise VerboseException(
            'no asset id or asset url is given for insert_picture')

    filename = None
    use_connector_url = False

    if asset_url is not None:
        try:
            # download the image file, save it in the export asset folder
            m = hashlib.sha1(asset_url)
            filename = '%s/%s' % (exp_files_path, str(m.hexdigest()))

            url_parts = asset_url.split('/')
            if len(url_parts) > 1:
                filename += '.%s' % url_parts[-1]

            urllib.urlretrieve(asset_url, filename)
            use_connector_url = True
        except Exception as e:
            raise VerboseException(
                'could not download connector image: %s' % str(e))
    else:
        for _file in exp_files:
            if _file['eas_id'] == eas_id:
                filename = os.path.abspath(
                    '%s/%s' % (exp_files_path, _file['path']))
                break
        if filename is None:
            raise VerboseException(
                'could not find asset with id %d in export files' % eas_id)

    try:
        img = Image.open(filename)
    except Exception as e:
        if use_connector_url:
            raise VerboseException(
                'could not load connector image: %s' % str(e))
        else:
            raise VerboseException(
                'could not load exported image from local instance slide: %s' % str(e))

    try:
        # get placeholder size in emus
        pw_emu = float(placeholder.width)
        ph_emu = float(placeholder.height)

        iw, ih = img.size

        # convert image size from pixels to emus
        iw_emu = pixels_to_emu(iw)
        ih_emu = pixels_to_emu(ih)

        h_ratio = iw_emu / pw_emu
        w_ratio = ih_emu / ph_emu

        # scale down to fit the longer image side into the shorter placeholder side
        new_x = 0
        new_y = 0
        new_h = 0
        new_w = 0
        if h_ratio >= w_ratio:
            new_h = int(ih_emu / h_ratio)
            new_w = int(iw_emu / h_ratio)
            new_y = (ph_emu - new_h) / 2
        else:
            new_h = int(ih_emu / w_ratio)
            new_w = int(iw_emu / w_ratio)
            new_x = (pw_emu - new_w) / 2

        shapes.add_picture(filename, new_x + placeholder.left,
                           new_y + placeholder.top, height=new_h)

        picture_bottom_line = new_y + placeholder.top + new_h

        # remove the original placeholder since it is not needed
        placeholder._element.getparent().remove(placeholder._element)
    except Exception as e:
        placeholder.insert_picture(filename)

    return picture_bottom_line


def create_missing_dirs(f_path):
    base_dir = '/'.join(f_path.split('/')[:-1])
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
