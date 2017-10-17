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
            filename = os.path.join(self._datafolder, self._data['parameters']['file'])
            file = RasterFile(filename=filename)

            if not file.is_valid():
                return dict(
                    status_code=404,
                    body="File not found or not valid."
                )

            return dict(
                status_code=200,
                body={
                    'metadata': file.get_metadata(),
                    'data': file.get_data()
                }
            )

        return dict(
            status_code=500,
            body="Internal Server Error. Request data does not fit."
        )
