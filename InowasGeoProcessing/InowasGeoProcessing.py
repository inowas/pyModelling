import os
from .RasterFile import RasterFile

"""
This module offers some helpers por geoprocessing

Author: Ralf Junghanns
EMail: ralf.junghanns@gmail.com
"""


class InowasGeoProcessing:

    _data = None
    _datafolder = None

    def __init__(self, datafolder, data):
        self._data = data
        self._datafolder = datafolder
        pass

    def response(self):

        if self._data['method'] == 'extractRasterData':
            print('Method: extractRasterData')

            if 'parameters' not in self._data:
                return dict(
                    status_code=422,
                    body="Invalid argument exception, key: 'parameters' not given."
                )

            parameters = self._data['parameters']

            if 'file' not in parameters:
                return dict(
                    status_code=422,
                    body="Invalid argument exception, key: 'file' not found in parameters."
                )

            filename = os.path.join(self._datafolder, self._data['parameters']['file'])
            file = RasterFile(filename=filename)

            if not file.is_valid():
                return dict(
                    status_code=404,
                    body="File not found or not valid."
                )

            width = False
            if 'width' in parameters:
                width = parameters['width']

            height = False
            if 'height' in parameters:
                height = parameters['height']

            available_interpolation_methods = [
                'nearest', 'linear', 'cubic'
            ]

            method = available_interpolation_methods[0]
            if 'method' in parameters:
                method = parameters['method']
                if parameters['method'] not in available_interpolation_methods:
                    return dict(
                        status_code=422,
                        body="Invalid argument exception, interpolation method: {} not available. "
                             "Available methods are {}.".format(method, ', '.join(available_interpolation_methods))
                    )

            return dict(
                status_code=200,
                body={
                    'metadata': file.get_metadata(),
                    'data': file.get_data(width=width, height=height, method=method)
                }
            )

        return dict(
            status_code=500,
            body="Internal Server Error. Request data does not fit."
        )
