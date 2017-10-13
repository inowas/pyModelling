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

        info = ""
        info += "Driver: {}/{}{}".format(
            self._dataset.GetDriver().ShortName,
            self._dataset.GetDriver().LongName,
            "\r\n"
        )

        info += "Size: {} x {} x {}{}".format(
            self._dataset.RasterXSize,
            self._dataset.RasterYSize,
            self._dataset.RasterCount,
            "\r\n"
        )

        info += "Projection: {}{}".format(self._dataset.GetProjection(), "\r\n")

        geotransform = self._dataset.GetGeoTransform()
        if geotransform:
            info += "Origin = ({}, {}){}".format(geotransform[0], geotransform[3], "\r\n")
            info += "Pixel Size = ({}, {}){}".format(geotransform[1], geotransform[5], "\r\n")

        return info

    def get_data(self):
        if not self.is_valid():
            raise FileNotFoundError('File not valid.')

        data = []
        for iBand in range(1, self._dataset.RasterCount+1):
            band = self._dataset.GetRasterBand(iBand)
            data.append(band.ReadAsArray().tolist())

        return data
