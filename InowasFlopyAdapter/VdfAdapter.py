import flopy.seawat as swt


class VdfAdapater:
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
            if not key.startswith('_'):
                default[key] = self._data[key]
        return default

    def get_package(self):
        content = self.merge()
        return swt.SeawatVdf(
            **content
        )

    @staticmethod
    def default():
        default = {
            "mtdnconc": 1,
            "mfnadvfd" = 1,
            "nswtcpl" = 1,
            "iwtable" = 1,
            "densemin" = 1.000,
            "densemax" = 1.025,
            "dnscrit" = 1e-2,
            "denseref" = 1.000,
            "denseslp" = .025,
            "crhoref" = 0,
            "firstdt" = 0.001,
            "indense" = 1,
            "dense" = 1.000,
            "nsrhoeos" = 1,
            "drhodprhd" = 4.46e-3,
            "prhdref" = 0.,
            "extension" = 'vdf',
            "unitnumber" = None,
            "filenames" = None,
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "mtdnconc": package.mtdnconc,
            "mfnadvfd": package.mfnadvfd,
            "nswtcpl": package.nswtcpl,
            "iwtable": package.iwtable,
            "densemin": package.densemin,
            "densemax": package.densemax,
            "dnscrit": package.dnscrit,
            "denseref": package.denseref,
            "denseslp": package.denseslp,
            "crhoref": package.crhoref,
            "firstdt": package.firstdt,
            "indense": package.indense,
            "dense": package.dense,
            "nsrhoeos": package.nsrhoeos,
            "drhodprhd": package.drhodprhd,
            "prhdref": package.prhdref,
            "extension": package.extension,
            "unitnumber": package.unitnumber,
            "filenames": package.filenames,
        }
        return content
