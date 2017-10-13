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

        response = None

        if self._data['method'] == 'extractRasterData':
            print('Method: extractRasterData')
            file = RasterFile(filename=self._data['parameter']['file'])

            if not file.is_valid():
                return dict(
                    status_code=404,
                    message="File not found or not valid."
                )

            response = {'info': file.get_metadata(), 'data': file.get_data()}

        if response is not None:
            return dict(
                status_code=200,
                response=response
            )

        return dict(
            status_code=500,
            message="Internal Server Error. Request data does not fit."
        )
