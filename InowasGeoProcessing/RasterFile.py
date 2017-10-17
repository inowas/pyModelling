import gdal


class RasterFile:

    _filename = None
    _dataset = None

    def __init__(self, filename):
        self._filename = filename
        self._dataset = gdal.Open(self._filename, gdal.GA_ReadOnly)

    def is_valid(self):
        if type(self._dataset) is not gdal.Dataset:
            return False

        return True

    def get_metadata(self):
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

    def get_data(self):
        if not self.is_valid():
            raise FileNotFoundError('File not valid.')

        data = []
        for iBand in range(1, self._dataset.RasterCount+1):
            band = self._dataset.GetRasterBand(iBand)
            data.append(band.ReadAsArray().tolist())

        return data
