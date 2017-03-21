import flopy.modflow as mf


class OcAdapter:

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
        return mf.ModflowOc(
                _mf,
                ihedfm=content['ihedfm'],
                iddnfm=content['iddnfm'],
                chedfm=content['chedfm'],
                cddnfm=content['cddnfm'],
                cboufm=content['cboufm'],
                compact=content['compact'],
                stress_period_data=self.get_stress_period_data(content['stress_period_data']),
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def default():
        default = {
            "ihedfm": 0,
            "iddnfm": 0,
            "chedfm": None,
            "cddnfm": None,
            "cboufm": None,
            "compact": True,
            "stress_period_data": {(0, 0): ['save head']},
            "extension": ['oc', 'hds', 'ddn', 'cbc'],
            "unitnumber": [14, 51, 52, 53]
        }

        return default

    @staticmethod
    def get_stress_period_data(stress_periods):
        stress_period_data = {}
        for stress_period in stress_periods:
            stress_period_data[stress_period['stressPeriod'], stress_period['timeStep']] = stress_period['type']

        return stress_period_data
