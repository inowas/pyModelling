import flopy.mt3d as mt


class SsmAdapter:

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

    def get_package(self, _mt):
        content = self.merge()
        return mt.Mt3dSsm(
                _mt,
                **content
            )

    @staticmethod
    def default():
        #Problem with mxss if used default None calculated incorrectly
        default = {
            "crch": None,
            "cevt": None,
            "mxss": None,
            "stress_period_data": None,
            "dtype": None,
            "extension": 'ssm',
            "unitnumber": None,
            "filenames": None
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "crch": package.crch,
            "cevt": package.cevt,
            "mxss": package.mxss,
            "stress_period_data": package.stress_period_data,
            "dtype": package.dtype,
            "extension": package.extension,
            "unitnumber": package.unitnumber,
            "filenames": package.filenames
        }
        return content
        
