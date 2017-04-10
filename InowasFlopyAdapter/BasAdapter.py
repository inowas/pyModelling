import flopy.modflow as mf


class BasAdapter:

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
        content = self.default()
        return mf.ModflowBas(
                _mf,
                ibound=content['ibound'],
                strt=content['strt'],
                ifrefm=content['ifrefm'],
                ixsec=content['ixsec'],
                ichflg=content['ichflg'],
                stoper=content['stoper'],
                hnoflo=content['hnoflo'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def default():
        default = {
            "ibound": 1,
            "strt": 1.0,
            "ifrefm": True,
            "ixsec": False,
            "ichflg": False,
            "stoper": None,
            "hnoflo": -999.99,
            "extension": 'bas',
            "unitnumber": 13
        }

        return default
