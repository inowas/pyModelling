import json
import os
import sys
from InowasFlopyAdapter.InowasFlopyAdapter import InowasFlopyAdapter


def main():
    filename = os.path.realpath(sys.argv[1])
    print('This script loads file: %s' % filename)

    dirname = os.path.dirname(filename)
    os.chdir(dirname)
    print('Change to directory: %s' % print(dirname))

    with open(filename) as data_file:
        content = json.load(data_file)

    author = content.get("author")
    project = content.get("project")
    calculation_type = content.get("type")
    version = content.get("version")
    data = content.get("data")

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Type: %s' % calculation_type)
    print('Version: %s' % version)

    if calculation_type == 'flopy':
        print('Running flopy:')
        flopy = InowasFlopyAdapter(version, data)


if __name__ == '__main__':
    main()
