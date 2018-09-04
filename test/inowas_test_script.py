import numpy
import json
import os
import sys
from InowasFlopyAdapter.InowasFlopyCalculationAdapter import InowasFlopyCalculationAdapter
from InowasFlopyAdapter.InowasFlopyReadAdapter import InowasFlopyReadAdapter
from InowasInterpolation import Gaussian

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

    if m_type == 'flopy_calculation':
        print("Running flopy calculation for model-id '{0}' with calculation-id '{1}'".format(model_id, calculation_id))
        target_directory = os.path.join(datafolder, calculation_id)
        print('The target directory is %s' % target_directory)

        print('Write config to %s' % os.path.join(target_directory, 'configuration.json'))
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        with open(os.path.join(target_directory, 'configuration.json'), 'w') as outfile:
            json.dump(content, outfile)

        data['mf']['mf']['modelname'] = 'mf'
        data['mf']['mf']['model_ws'] = target_directory

        if 'mt' in data:
            data['mt']['mt']['modelname'] = 'mt'
            data['mt']['mt']['model_ws'] = target_directory

        flopy = InowasFlopyCalculationAdapter(version, data, calculation_id)
        response = {}
        response['status_code'] = "200"
        response['model_id'] = model_id
        response['calculation_id'] = calculation_id
        response['data'] = flopy.response()
        response['message'] = flopy.response_message()
        response = str(response).replace('\'', '"')
        return response

    if m_type == 'flopy_read_data':
        print('Read flopy data:')
        calculation_id = content.get("calculation_id")
        project_folder = os.path.join(datafolder, calculation_id)
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
    print('Change to directory: %s' % dirname)

    with open(filename) as data_file:
        content = json.load(data_file)

    response = process(content, datafolder)
    print(response)


if __name__ == '__main__':
    main()
