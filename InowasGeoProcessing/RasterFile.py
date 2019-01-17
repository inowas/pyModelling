from osgeo import gdal
from skimage.transform import resize


class RasterFile:
    _filename = None
    _dataset = None

    def __init__(self, filename):
        self._filename = filename
        print('RasterFile filename: %s' % filename)

    def open_file(self):
        self._dataset = gdal.Open(self._filename, gdal.GA_ReadOnly)
        print('RasterFile dataset: %s' % self._dataset)

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

    def get_data(self, width=False, height=False, method='wrap'):
        self.open_file()
        if not self.is_valid():
            raise FileNotFoundError('File not valid.')

        data = []
        for iBand in range(1, self._dataset.RasterCount + 1):
            band = self._dataset.GetRasterBand(iBand)
            band_data = band.ReadAsArray()

            if width and height:
                band_data = self.interpolate(data2d=band_data, target_width=width, target_height=height, method=method)

            data.append(band_data.tolist())

        return data

    @staticmethod
    def interpolate(data2d, target_width, target_height, method):
        return resize(data2d, (int(target_height), int(target_width)), mode=method, preserve_range=True)
