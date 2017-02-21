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

    logger.debug("----%s-----" % plugin["name"])
    # logger.debug(json.dumps(plugin, indent = 2))
    logger.debug("------")
    logger.debug("%s" % json.dumps(produce_opts, indent = 2))
    logger.debug("------")
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


    def insert_picture(placeholder, gid):

        try:
            eas_id = data_by_gid[gid]["asset_ids"][0]
        except(IndexError, KeyError):
            logger.warn("No EAS-ID found for GID %s" % gid)
            return

        logger.debug("EAS-ID %s found for GID %s." % (eas_id, gid))

        for _file in  exp.getFiles():
            if _file["eas_id"] == eas_id:
                placeholder.insert_picture(exp.getFilesPath()+"/"+_file["path"])
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
                               slide["center"]["global_object_id"])

        if stype == "duo":
            if "global_object_id" in slide["left"]:
                if show_info:
                    insert_info(ppt_slide.placeholders[sl_info["text_left"]],
                                slide["left"]["global_object_id"])
                insert_picture(ppt_slide.placeholders[sl_info["picture_left"]],
                               slide["left"]["global_object_id"])

            if "global_object_id" in slide["right"]:
                if show_info:
                    insert_info(ppt_slide.placeholders[sl_info["text_right"]],
                                slide["right"]["global_object_id"])
                insert_picture(ppt_slide.placeholders[sl_info["picture_right"]],
                               slide["right"]["global_object_id"])


    pack_dir = easydb_context.get_temp_dir()
    pptx_filename = pack_dir+"/produce.pptx"
    target_filename = produce_opts["presentation"]["filename"]+".pptx"

    prs.save(pptx_filename)
    exp.addFile(pptx_filename, target_filename)






    return

    op = plugin["offlineplayer"]

    pack_dir = easydb_context.get_temp_dir()

    basepath = os.path.abspath(os.path.dirname(__file__))

    json_files = []

    for _file in  exp.getFiles():
        fn_split = os.path.splitext(_file["path"])
        if fn_split[1] != ".json":
            continue
        barename = os.path.basename(fn_split[0])
        json_files.append({"barename": barename, "path": _file["path"]})

    json_files_remove = []

    for _file in exp.getFiles():
        fn_split = os.path.splitext(_file["path"])
        if fn_split[1] == ".json":
            continue

        found_license = None
        for _license in produce_opts["licenses"]:
            [_cls, _version] = _license["drm_lizenzen"]["version"].split(".")
            if (_license["drm_lizenzen"]["eas_id"] == _file["eas_id"]
                and _cls == _file["eas_fileclass"]
                and _version == _file["eas_version"]):
                found_license = _license

        if not found_license:
            logger.debug("Skipping file %s, no license found." % _file["path"])
            continue

        barename = os.path.basename(fn_split[0])
        logger.debug("Producing .exe for %s%s." % (exp.getFilesPath(), _file))

        if os.path.isdir(pack_dir+"/files"):
            shutil.rmtree(pack_dir+"/files")

        logger.debug("file: %s" % _file)
        info = {
            "files": [],
            "licenses": [ found_license ],
            "tester": "henk'horst'"
            }

        # pack the CUI app into app.nw
        myzip = zipfile.ZipFile(pack_dir+"/app.nw", "w")

        for __file in op["app"]["files"]:
            fn = basepath+"/"+op["app"]["path"]+"/"+__file
            myzip.write(fn, __file)

        # add file from export
        fn = exp.getFilesPath()+"/"+_file["path"]
        name_in_zip = "files/"+os.path.basename(_file["path"])
        myzip.write(fn, name_in_zip)
        info["files"].append({"path": name_in_zip, "size": _file["size"]})

        logger.debug("Removing file: %s" % _file["path"])
        exp.removeFile(_file["path"])

        for __file in exp.getFiles():
            logger.debug("file after removal: %s" % __file)

        for json_file in json_files:
            logger.debug("name in zip: %s, json_file barename: %s" % (name_in_zip, json_file["barename"]))
            if name_in_zip.startswith("files/"+json_file["barename"]):
                json_in_zip = "files/"+os.path.basename(fn_split[0])+".json"
                json_file_path = exp.getFilesPath()+"/"+json_file["path"]
                if not json_file["path"] in json_files_remove:
                    json_files_remove.append(json_file["path"])
                myzip.write(json_file_path, json_in_zip)

        myzip.writestr("info.js", "var info="+json.dumps(info)+";")
        myzip.close()

        # create merged nw.exe and copy all necessary file to our pack directory
        path = basepath+"/"+op["nw.js"]["path"]

        files = []

        add_file(path+"/"+op["nw.js"]["nw.exe"], "video.exe")
        files.append(u"video.exe")

        f = open(pack_dir+"/video.exe", "ab")
        fi = open(pack_dir+"/app.nw", "rb")
        f.write(fi.read())
        fi.close()
        f.close()

        for __file in op["nw.js"]["files"]:
            add_file(path+"/"+__file, __file)
            files.append(__file)

        # os.remove(pack_dir+"/app.nw")

        call = [basepath+"/"+op["7z.exe"], "a", "-mx=0", "video.7z"]
        for __file in files:
            call.append(__file)

        p = subprocess.Popen(
            call,
            cwd=pack_dir,
            # shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )

        (out, err) = p.communicate()
        returncode = p.returncode

        f = open(pack_dir+"/video_all.exe", "ab")
        # add starter
        fi = open(basepath+"/"+op["7zsd.sfx"], "rb")
        f.write(fi.read())
        fi.close()
        # add config
        fi = open(basepath+"/"+op["config.txt"], "rb")
        f.write(fi.read())
        fi.close()
        # add video
        fi = open(pack_dir+"/video.7z", "rb")
        f.write(fi.read())
        fi.close()
        f.close()

        exp.addFile(pack_dir+"/video_all.exe", os.path.basename(fn_split[0])+".exe")
        logger.debug("produced: %s for %s " % (pack_dir+"/video_all.exe", _file))


    logger.debug("Removing %s" % json_files_remove)

    for file_path in json_files_remove:
        logger.debug("Removing file: %s" % file_path)
        exp.removeFile(file_path)

    return
