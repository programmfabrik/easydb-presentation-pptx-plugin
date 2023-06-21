import traceback
import shared


def easydb_server_start(easydb_context):
    easydb_context.register_callback('export_produce', {
        'callback': 'produce_files',
    })


def produce_files(easydb_context, parameters, protocol=None):
    try:
        exp = easydb_context.get_exporter()
        produce_opts = exp.getExport()['export']['produce_options']

        if 'pptx' not in produce_opts:
            return

        pack_dir = easydb_context.get_temp_dir()
        pptx_filename = '{0}/produce.pptx'.format(pack_dir)
        target_filename = shared.parse_target_filename(produce_opts)

        shared.produce_files(
            produce_opts,
            exp.getFilesPath(),
            exp.getFiles(),
            pptx_filename)

        exp.addFile(pptx_filename, target_filename)

    except Exception as e:
        traceback.print_exc()
        raise e
