import flopy.mt3d as mt


class DspAdapter:

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
        return mt.Mt3dDsp(
                _mt,
                **content
            )

    @staticmethod
    def default():
        default = {
            "al": 0.01,
            "trpt": 0.1,
            "trpv": 0.01,
            "dmcoef": 1e-09,
            "extension": 'dsp',
            "multiDiff": False,
            "unitnumber": None,
            "filenames": None
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "al": package.al,
            "trpt": package.trpt,
            "trpv": package.trpv,
            "dmcoef": package.dmcoef,
            "extension": package.extension,
            "multiDiff": package.multiDiff,
            "unitnumber": package.unitnumber,
            "filenames": package.filenames
        }
        return content
        
