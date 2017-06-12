import numpy
import json
import os
import sys
import traceback
from InowasFlopyAdapter.InowasFlopyCalculationAdapter import InowasFlopyCalculationAdapter
from InowasFlopyAdapter.InowasFlopyReadAdapter import InowasFlopyReadAdapter
from InowasInterpolation import Gaussian

scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, 'bin')


def process(content, datafolder):
    author = content.get("author")
    project = content.get("project")
    uuid = content.get("id")
    m_type = content.get("type")
    version = content.get("version")

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Uuid: %s' % uuid)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy_calculation':
        print('Running flopy calculation with id: %s' % uuid)

        target_directory = os.path.join(datafolder, uuid)
        print('The target directory is %s' % target_directory)
        
        print('Write config to %s' % os.path.join(target_directory, 'configuration.json'))
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        with open(os.path.join(target_directory, 'configuration.json'), 'w') as outfile:
            json.dump(content, outfile)

        data = content.get("data")
        data['mf']['model_ws'] = target_directory
        data['mf']['exe_name'] = os.path.join(binfolder, sys.platform, data['mf']['exe_name'])
        print(data['mf']['exe_name'])

        try:
            flopy = InowasFlopyCalculationAdapter(version, data, uuid)
            return flopy.response()
        except:
            response = dict(
                status_code=500,
                calculation_id=uuid,
                message=str(traceback.format_exc()).replace('"', '\"')
            )
            print(json.dumps(response))
            return response

    if m_type == 'flopy_read_data':
        print('Read flopy data:')
        project_folder = os.path.join(datafolder, uuid)
        flopy = InowasFlopyReadAdapter(version, project_folder, content.get("request"))
        print(json.dumps(flopy.response()))
        return flopy.response()

    if m_type == 'interpolation':
        print('Running interpolation:')
        if 'gaussian' in content.get("data")['methods']:
            interpolation = Gaussian.Gaussian(content.get("data"))
            result = interpolation.calculate()
            if isinstance(result, numpy.ndarray):
                print(result)


def main():
    datafolder = os.path.realpath(sys.argv[1])

    filename = os.path.realpath(sys.argv[2])
    print('This script loads file: %s' % filename)

    dirname = os.path.dirname(filename)
    os.chdir(dirname)
    print('Change to directory: %s' % print(dirname))

    with open(filename) as data_file:
        content = json.load(data_file)

    process(content, datafolder)

if __name__ == '__main__':
    main()
