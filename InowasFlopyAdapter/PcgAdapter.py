import flopy.modflow as mf


class PcgAdapter:

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
        return mf.ModflowPcg(
                _mf,
                mxiter=content['mxiter'],
                iter1=content['iter1'],
                npcond=content['npcond'],
                hclose=content['hclose'],
                rclose=content['rclose'],
                relax=content['relax'],
                nbpol=content['nbpol'],
                iprpcg=content['iprpcg'],
                mutpcg=content['mutpcg'],
                damp=content['damp'],
                dampt=content['dampt'],
                ihcofadd=content['ihcofadd'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def default():
        default = {
            "mxiter": 50,
            "iter1": 30,
            "npcond": 1,
            "hclose": 1E-5,
            "rclose": 1E-5,
            "relax": 1.0,
            "nbpol": 0,
            "iprpcg": 0,
            "mutpcg": 3,
            "damp": 1.0,
            "dampt": 1.0,
            "ihcofadd": 0,
            "extension": 'pcg',
            "unitnumber": 27
        }

        return default