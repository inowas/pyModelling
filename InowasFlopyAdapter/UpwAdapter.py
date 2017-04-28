import flopy.modflow as mf


class UpwAdapter:

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
        return mf.ModflowUpw(
                _mf,
                laytyp=content['laytyp'],
                layavg=content['layavg'],
                chani=content['chani'],
                layvka=content['layvka'],
                laywet=content['laywet'],
                ipakcb=content['ipakcb'],
                hdry=content['hdry'],
                iphdry=content['iphdry'],
                hk=content['hk'],
                hani=content['hani'],
                vka=content['vka'],
                ss=content['ss'],
                sy=content['sy'],
                vkcb=content['vkcb'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def default():
        default = {
            "laytyp": 0,
            "layavg": 0,
            "chani": 1.0,
            "layvka": 0,
            "laywet": 0,
            "ipakcb": 53,
            "hdry": -1e+30,
            "iphdry": 0,
            "hk": 1.0,
            "hani": 1.0,
            "vka": 1.0,
            "ss": 1e-5,
            "sy": 0.15,
            "vkcb": 0.0,
            "extension": 'upw',
            "unitnumber": 31
        }

        return default
