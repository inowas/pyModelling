import gdal
import numpy as np
from scipy.interpolate import griddata


class RasterFile:

    _filename = None
    _dataset = None

    def __init__(self, filename):
        self._filename = filename

    def open_file(self):
        self._dataset = gdal.Open(self._filename, gdal.GA_ReadOnly)

    def is_valid(self):
        self.open_file()
        if type(self._dataset) is not gdal.Dataset:
            return False

        return True

    def get_metadata(self):
        self.open_file()
        if not self.is_valid():
            raise FileNotFoundError('File not valid.')

        metadata = {
            'driver': self._dataset.GetDriver().ShortName,
            'rasterXSize': self._dataset.RasterXSize,
            'rasterYSize': self._dataset.RasterYSize,
            'rasterCount': self._dataset.RasterCount,
            'projection': self._dataset.GetProjection()
        }

        geotransform = self._dataset.GetGeoTransform()
        if geotransform:
            metadata['origin'] = [geotransform[0], geotransform[3]]
            metadata['pixelSize'] = [geotransform[1], geotransform[5]]

        return metadata

    def get_data(self, width=False, height=False, method='nearest'):
        self.open_file()
        if not self.is_valid():
            raise FileNotFoundError('File not valid.')

        data = []
        for iBand in range(1, self._dataset.RasterCount+1):
            band = self._dataset.GetRasterBand(iBand)
            band_data = band.ReadAsArray()

            if width and height:
                band_data = self.interpolate(data2d=band_data, width=width, height=height, method=method)

            data.append(band_data.tolist())

        return data

    @staticmethod
    def interpolate(data2d, width, height, method):

        if len(data2d) == height and len(data2d[0]) == width:
            return data2d

        grid_x, grid_y = np.mgrid[0:len(data2d[0]):complex(height), 0:len(data2d):complex(width)]
        points = np.indices((len(data2d), len(data2d[0]))).T.reshape(-1, 2)
        values = data2d.flatten('F')
        return griddata(points, values, (grid_x, grid_y), method=method)
