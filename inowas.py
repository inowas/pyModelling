import numpy
import json
import os
import sys
from InowasFlopyAdapter.InowasFlopyAdapter import InowasFlopyAdapter
from InowasInterpolation import Gaussian


def process(content):
    author = content.get("author")
    project = content.get("project")
    m_type = content.get("type")
    version = content.get("version")
    data = content.get("data")

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy':
        print('Running flopy:')
        flopy = InowasFlopyAdapter(version, data)

    if m_type == 'interpolation':
        print('Running interpolation:')

        if 'gaussian' in data['methods']:
            interpolation = Gaussian.Gaussian(data)
            result = interpolation.calculate()
            if isinstance(result, numpy.ndarray):
                print(result)


def main():
    filename = os.path.realpath(sys.argv[1])
    print('This script loads file: %s' % filename)

    dirname = os.path.dirname(filename)
    os.chdir(dirname)
    print('Change to directory: %s' % print(dirname))

    with open(filename) as data_file:
        content = json.load(data_file)

    process(content)

if __name__ == '__main__':
    main()
