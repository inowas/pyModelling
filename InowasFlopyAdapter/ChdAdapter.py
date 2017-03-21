import flopy.modflow as mf


class ChdAdapter:

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
        return mf.ModflowChd(
                _mf,
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def default():
        default = {
            "stress_period_data": None,
            "dtype": None,
            "extension": 'chd',
            "unitnumber": 24
        }

        return default
