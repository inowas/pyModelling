import flopy.modflow as mf


class DisAdapter:

    _data = None

    def __init__(self, data):
        self._data = data

    def validate(self):
        # should be implemented
        # for key in content:
        #   do something
        #   return some hints
        pass

    def is_valid(self):
        # should be implemented
        # for key in content:
        #   do something
        #   return true or false
        return True

    def merge(self):
        default = self.default()
        for key in self._data:
            default[key] = self._data[key]
        return default

    def get_package(self, _mf):
        content = self.merge()
        return mf.ModflowDis(
            _mf,
            nlay=content['nlay'],
            nrow=content['nrow'],
            ncol=content['ncol'],
            nper=content['nper'],
            delr=content['delr'],
            delc=content['delc'],
            laycbd=content['laycbd'],
            top=content['top'],
            botm=content['botm'],
            perlen=content['perlen'],
            nstp=content['nstp'],
            tsmult=content['tsmult'],
            steady=content['steady'],
            itmuni=content['itmuni'],
            lenuni=content['lenuni'],
            extension=content['extension'],
            unitnumber=content['unitnumber'],
            xul=content['xul'],
            yul=content['yul'],
            rotation=content['rotation'],
            proj4_str=content['proj4_str'],
            start_datetime=content['start_datetime']
        )

    @staticmethod
    def default():
        default = {
            "nlay": 1,
            "nrow": 2,
            "ncol": 2,
            "nper": 1,
            "delr": 1.0,
            "delc": 1.0,
            "laycbd": 0,
            "top": 1,
            "botm": 0,
            "perlen": 1,
            "nstp": 1,
            "tsmult": 1,
            "steady": True,
            "itmuni": 4,
            "lenuni": 2,
            "extension": 'dis',
            "unitnumber": 11,
            "xul": None,
            "yul": None,
            "rotation": 0.0,
            "proj4_str": None,
            "start_datetime": None
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "nlay": package.nlay,
            "nrow": package.nrow,
            "ncol": package.ncol,
            "nper": package.nper,
            "delr": package.delr,
            "delc": package.delc,
            "laycbd": package.laycbd,
            "top": package.top,
            "botm": package.botm,
            "perlen": package.perlen,
            "nstp": package.nstp,
            "tsmult": package.tsmult,
            "steady": package.steady,
            "itmuni": package.itmuni,
            "lenuni": package.lenuni,
            "extension": package.extension,
            "unitnumber": package.unitnumber,
            "xul": package.xul,
            "yul": package.yul,
            "rotation": package.rotation,
            "proj4_str": package.proj4_str,
            "start_datetime": package.start_datetime
        }
        return content