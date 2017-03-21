import flopy.modflow as mf


class WelAdapter:

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
        return mf.ModflowWel(
                _mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                options=content['options']
            )

    @staticmethod
    def default():
        default = {
            "ipakcb": 0,
            "stress_period_data": None,
            "dtype": None,
            "extension": 'wel',
            "unitnumber": 20,
            "options": None
        }

        return default
