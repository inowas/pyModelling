import json
import os
import sys

from InowasGeoProcessing.InowasGeoProcessing import InowasGeoProcessing

scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, 'bin')


def process(content, datafolder):
    author = content.get("author")
    project = content.get("project")
    calculation_id = content.get("calculation_id")
    model_id = content.get("model_id")
    m_type = content.get("type")
    version = content.get("version")
    data = content.get("data")

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Model Id: %s' % model_id)
    print('Calculation Id: %s' % calculation_id)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'geoProcessing':
        print('Running geoProcessing:')
        gp = InowasGeoProcessing(datafolder, data)
        response = gp.response()
        print(json.dumps(response))


def main():
    datafolder = os.path.realpath(sys.argv[1])

    filename = os.path.realpath(sys.argv[2])
    print('This script loads file: %s' % filename)

    dirname = os.path.dirname(filename)
    os.chdir(dirname)
    print('Change to directory: %s' % print(dirname))

    with open(filename) as data_file:
        content = json.load(data_file)

    response = process(content, datafolder)
    print(response)


if __name__ == '__main__':
    main()
