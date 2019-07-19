import os
import hashlib
import urllib

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

from PIL import Image
from context import get_json_value


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger('presentation-pptx')
    logger.debug('PPTX started')

    easydb_context.register_callback('export_produce', {
        'callback': 'produce_files',
    })


def produce_files(easydb_context, parameters, protocol=None):
    global pack_dir

    exp = easydb_context.get_exporter()
    produce_opts = exp.getExport()['export']['produce_options']
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

    standard_format = {
        '1': {
            'size': 30,
            'bold': True
        },
        '2': {
            'size': 24,
            'bold': False
        },
        '3': {
            'size': 20,
            'bold': False
        }
    }

    show_standard = []
    if 'show_standard' in produce_opts['presentation']['settings']:
        show_standard = [s.strip() for s in produce_opts['presentation']['settings']['show_standard'].split(' ')]

    prs = Presentation('%s/%s' % (basepath, produce_opts['pptx_form']['template']['name']))

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

    data_by_gid = produce_opts['presentation']['data_by_gid']

    def insert_info(placeholder, shapes, gid):
        if gid not in data_by_gid:
            return

        text_box = shapes.add_textbox(placeholder.left, placeholder.top, placeholder.width, placeholder.height)

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
                p.font.name = 'FreeSans'
                p.font.size = Pt(standard_format[s]['size'])
                p.font.bold = standard_format[s]['bold']

        # remove the original placeholder since it is not needed
        placeholder._element.getparent().remove(placeholder._element)

    def insert_picture(placeholder, shapes, eas_id, asset_url=None):

        if eas_id is None and asset_url is None:
            logger.warn('no asset id or asset url is given for insert_picture')
            return

        filename = None
        use_connector_url = False

        if asset_url is not None:
            try:
                # download the image file, save it in the export asset folder
                m = hashlib.sha1(asset_url)
                filename = '%s/%s' % (exp.getFilesPath(), str(m.hexdigest()))

                url_parts = asset_url.split('/')
                if len(url_parts) > 1:
                    filename += '.%s' % url_parts[-1]

                urllib.urlretrieve(asset_url, filename)
                use_connector_url = True
            except Exception as e:
                logger.warn('could not download connector image: %s' % str(e))
                return
        else:
            for _file in exp.getFiles():
                if _file['eas_id'] == eas_id:
                    filename = '%s/%s' % (exp.getFilesPath(), _file['path'])
                    break

        if filename is None:
            logger.debug('no asset file name could be found in insert_picture')
            return

        try:
            if use_connector_url:
                logger.debug('load connector image %s' % filename)
            else:
                logger.debug('load exported image from local instance %s' % filename)
            img = Image.open(filename)
        except Exception as e:
            if use_connector_url:
                logger.warn('could not load connector image: %s' % str(e))
            else:
                logger.warn('could not load exported image from local instance slide: %s' % str(e))
            return

        try:
            # get placeholder size in emus
            pw_emu = float(placeholder.width)
            ph_emu = float(placeholder.height)

            iw, ih = img.size

            # convert image size from pixels to emus
            dpi = 72
            iw_emu = float(iw * (914400 / dpi))
            ih_emu = float(ih * (914400 / dpi))

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

            shapes.add_picture(filename, new_x + placeholder.left, new_y + placeholder.top, height=new_h)

            # remove the original placeholder since it is not needed
            placeholder._element.getparent().remove(placeholder._element)
        except Exception as e:
            logger.warn('could not get image resolution / size information, will insert image %s into placeholder' % filename)
            placeholder.insert_picture(filename)

    for slide in produce_opts['presentation']['slides']:
        stype = slide['type']

        sl = slide_layouts[stype]
        sl_info = sl['info']

        print 'adding slide', stype, repr(sl_info), repr(slide)
        ppt_slide = prs.slides.add_slide(sl['layout'])

        if stype == 'start':
            ppt_slide.placeholders[sl_info['title']].text = slide['data']['title']
            ppt_slide.placeholders[sl_info['subtitle']].text = slide['data']['info']

        if stype == 'bullets':
            ppt_slide.placeholders[sl_info['title']].text = slide['data']['title']

            text_frame = ppt_slide.placeholders[sl_info['bullets']].text_frame
            text_frame.clear()  # remove any existing paragraphs, leaving one empty one

            rows = slide['data']['info'].split('\n')

            p = text_frame.paragraphs[0]
            p.text = rows[0]

            for row in rows[1:]:
                p = text_frame.add_paragraph()
                p.text = row

        if stype == 'one':
            if 'global_object_id' in slide['center']:

                insert_info(ppt_slide.placeholders[sl_info['text']],
                            ppt_slide.shapes,
                            slide['center']['global_object_id'])

                insert_picture(ppt_slide.placeholders[sl_info['picture']],
                               ppt_slide.shapes,
                               get_json_value(slide['center'], 'asset_id'),
                               get_json_value(slide['center'], 'asset_url'))

        if stype == 'duo':
            if 'global_object_id' in slide['left']:
                insert_info(ppt_slide.placeholders[sl_info['text_left']],
                            ppt_slide.shapes,
                            slide['left']['global_object_id'])

                insert_picture(ppt_slide.placeholders[sl_info['picture_left']],
                               ppt_slide.shapes,
                               get_json_value(slide['left'], 'asset_id'),
                               get_json_value(slide['left'], 'asset_url'))

            if 'global_object_id' in slide['right']:
                insert_info(ppt_slide.placeholders[sl_info['text_right']],
                            ppt_slide.shapes,
                            slide['right']['global_object_id'])

                insert_picture(ppt_slide.placeholders[sl_info['picture_right']],
                               ppt_slide.shapes,
                               get_json_value(slide['right'], 'asset_id'),
                               get_json_value(slide['right'], 'asset_url'))

    pack_dir = easydb_context.get_temp_dir()
    pptx_filename = '%s/produce.pptx' % pack_dir
    target_filename = '%s.pptx' % produce_opts['presentation']['filename']

    prs.save(pptx_filename)
    exp.addFile(pptx_filename, target_filename)
