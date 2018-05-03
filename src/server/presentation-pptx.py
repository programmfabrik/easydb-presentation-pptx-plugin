import subprocess
import os
import json
import getpass
import re
import glob
import zipfile
import shutil
import pprint
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
from context import get_json_value


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger('presentation-pptx')
    logger.debug('PPTX started')

    easydb_context.register_callback('export_produce', {
        'callback': 'produce_files',
    })

def produce_files(easydb_context, parameters, protocol = None):
    global pack_dir

    exp = easydb_context.get_exporter()
    produce_opts = exp.getExport()["export"]["produce_options"]
    logger = easydb_context.get_logger('export.pptx')

    if "pptx" not in produce_opts:
        return

    logger.debug('parameters: %s' % parameters)

    logger.debug("exp: %s" % exp)
    if not exp:
        logger.error("could not get exporter object")
        return

    for plugin in easydb_context.get_plugins()["plugins"]:
        if plugin["name"] == "presentation-pptx":
            break

    # logger.debug("----%s-----" % plugin["name"])
    # logger.debug(json.dumps(plugin, indent = 2))
    # logger.debug("------")
    # logger.debug("%s" % json.dumps(produce_opts, indent = 2))
    # logger.debug("------")
    # logger.debug("%s" % json.dumps(exp.getFiles(), indent = 2))

    # print "%s" % json.dumps(exp.getFiles(), indent = 2)

    # produce slides

    basepath = os.path.abspath(os.path.dirname(__file__))
    show_info = produce_opts["presentation"]["settings"]["show_info"] == "standard-info"

    prs = Presentation(basepath+"/"+produce_opts["pptx_form"]["template"]["name"])

    slide_layouts = {}

    for slide in produce_opts["pptx_form"]["template"]["slides"]:
        if show_info:
            if "show_info" in slide and slide["show_info"] == True:
                slide_layouts[slide["type"]] = {
                    "layout": prs.slide_layouts[slide["slide_idx"]],
                    "info": slide,
                    }
        else:
            if "show_info" not in slide or slide["show_info"] == False:
                slide_layouts[slide["type"]] = {
                    "layout": prs.slide_layouts[slide["slide_idx"]],
                    "info": slide,
                    }

    data_by_gid = produce_opts["presentation"]["data_by_gid"]

    def add_info_to_slide(ppt_slide, gid):
        if not show_info:
            return

        if gid not in data_by_gid:
            return

        if "1" in data_by_gid[gid]["standard_info"]:
            standard = data_by_gid[gid]["standard_info"]["1"]
            txBox = ppt_slide.shapes.add_textbox(left, top, width, height)
            txBox.text_frame.text = standard
            # print "  standard", standard

    def insert_info(placeholder, gid):
        if gid not in data_by_gid:
            return

        if "1" in data_by_gid[gid]["standard_info"]:
            standard = data_by_gid[gid]["standard_info"]["1"]
            placeholder.text_frame.text = standard
            # print "  standard", standard


    def insert_picture(placeholder, gid, shapes, asset_position = None):

        try:
            if asset_position is None:
                eas_id = data_by_gid[gid]["asset_ids"][0]
            else:
                eas_id = data_by_gid[gid]["asset_ids"][asset_position]
        except(IndexError, KeyError):
            logger.warn("No EAS-ID found for GID %s" % gid)
            return

        for _file in  exp.getFiles():
            if _file["eas_id"] == eas_id:
                filename = exp.getFilesPath() + "/" + _file["path"]

                try:
                    # get placeholder size in emus
                    pw_emu = float(placeholder.width)
                    ph_emu = float(placeholder.height)

                    img = Image.open(filename)
                    iw = img.width
                    ih = img.height
                    dpi = img.info["dpi"]

                    # convert image size from pixels to emus
                    iw_emu = float(iw * (914400 / dpi[0]))
                    ih_emu = float(ih * (914400 / dpi[1]))

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

                    logger.debug("remove placeholder, resize and position image directly in slide")
                    shapes.add_picture(filename, new_x + placeholder.left, new_y + placeholder.top, height = new_h)

                    # remove the original placeholder since it is not needed
                    placeholder._element.getparent().remove(placeholder._element)

                except Exception as e:
                    logger.warn("could not fit image into slide, will use placeholder: " + str(e))
                    # fallback: insert the picture without any resizing into the original placeholder
                    placeholder.insert_picture(filename)

                break

    for slide in produce_opts["presentation"]["slides"]:
        stype = slide["type"]

        sl = slide_layouts[stype]
        sl_info = sl["info"]

        # print "adding slide", stype, repr(sl_info), repr(slide)
        ppt_slide = prs.slides.add_slide(sl["layout"])

        if stype == "start":
            title = ppt_slide.placeholders[sl_info["title"]].text = slide["data"]["title"]
            subtitle = ppt_slide.placeholders[sl_info["subtitle"]].text = slide["data"]["info"]

        if stype == "bullets":
            title = ppt_slide.placeholders[sl_info["title"]].text = slide["data"]["title"]
            # bullets = ppt_slide.placeholders[sl_info["bullets"]].text = slide["data"]["info"]

            text_frame = ppt_slide.placeholders[sl_info["bullets"]].text_frame
            text_frame.clear()  # remove any existing paragraphs, leaving one empty one

            rows = slide["data"]["info"].split("\n")

            p = text_frame.paragraphs[0]
            p.text = rows[0]

            for row in rows[1:]:
                p = text_frame.add_paragraph()
                p.text = row

        if stype == "one":
            if "global_object_id" in slide["center"]:
                if show_info:
                    insert_info(ppt_slide.placeholders[sl_info["text"]],
                                slide["center"]["global_object_id"])
                insert_picture(ppt_slide.placeholders[sl_info["picture"]],
                               slide["center"]["global_object_id"],
                               ppt_slide.shapes,
                               get_json_value(slide["center"], "asset_position"))

        if stype == "duo":
            if "global_object_id" in slide["left"]:
                if show_info:
                    insert_info(ppt_slide.placeholders[sl_info["text_left"]],
                                slide["left"]["global_object_id"])
                insert_picture(ppt_slide.placeholders[sl_info["picture_left"]],
                               slide["left"]["global_object_id"],
                               ppt_slide.shapes,
                               get_json_value(slide["left"], "asset_position"))

            if "global_object_id" in slide["right"]:
                if show_info:
                    insert_info(ppt_slide.placeholders[sl_info["text_right"]],
                                slide["right"]["global_object_id"])
                insert_picture(ppt_slide.placeholders[sl_info["picture_right"]],
                               slide["right"]["global_object_id"],
                               ppt_slide.shapes,
                               get_json_value(slide["right"], "asset_position"))


    pack_dir = easydb_context.get_temp_dir()
    pptx_filename = pack_dir+"/produce.pptx"
    target_filename = produce_opts["presentation"]["filename"]+".pptx"

    prs.save(pptx_filename)
    exp.addFile(pptx_filename, target_filename)


