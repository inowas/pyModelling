import numpy
import json
import os
import sys
import traceback
from InowasFlopyAdapter.InowasFlopyImportAdapter import InowasFlopyImportAdapter



def process(model_ws, json_file, mf_namfile=None, mt_namfile=None):

    print('Model directory: %s' % model_ws)
    print('Modflow model: %s' % mf_namfile)
    print('Mt3d model: %s' % mt_namfile)

    import_adapter = InowasFlopyImportAdapter(
        model_ws=model_ws,
        json_file=json_file,
        mf_namfile=mf_namfile,
        mt_namfile=mt_namfile
    )
    import_adapter.serialize()
    return import_adapter.response_message


def main():
    model_ws = os.path.realpath(sys.argv[1])
    json_file = os.path.realpath(sys.argv[2])
    try:
        mf_namfile = sys.argv[3]
    except IndexError:
        mf_namfile = None
    try:
        mt_namfile = sys.argv[4]
    except IndexError:
        mt_namfile = None

    print(model_ws)
    response = process(model_ws, json_file, mf_namfile, mt_namfile)
    print(response)


if __name__ == '__main__':
    main()
