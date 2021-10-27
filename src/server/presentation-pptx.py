# encoding: utf-8

import os

from context import EasydbException
import util


# wrapper for the get_json_value function with exception handling
def get_json(js, path, expected=False):
    try:
        return util.get_json_value(js, path, expected)
    except Exception as e:
        raise EasydbException('internal', str(e))


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger('presentation-pptx')
    logger.debug('PPTX started')

    easydb_context.register_callback('export_produce', {
        'callback': 'produce_pptx',
    })


def produce_pptx(easydb_context, parameters):
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

    pptx_filename = '%s/produce.pptx' % easydb_context.get_temp_dir()

    try:
        util.produce_files(
            produce_opts,
            exp.getFilesPath(),
            exp.getFiles(),
            pptx_filename)
    except util.VerboseException as e:
        logger.error(str(e))

    target_filename = util.parse_target_filename(produce_opts)
    exp.addFile(pptx_filename, target_filename)
