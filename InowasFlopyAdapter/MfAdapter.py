import flopy.modflow as mf


class MfAdapter:

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

    def get_package(self):
        content = self.merge()

        return mf.Modflow(
            modelname=content['modelname'],
            namefile_ext=content['namefile_ext'],
            version=content['version'],
            exe_name=content['exe_name'],
            structured=content['structured'],
            listunit=content['listunit'],
            model_ws=content['model_ws'],
            external_path=content['external_path'],
            verbose=content['verbose']
        )

    @staticmethod
    def default():
        default = {
            "modelname": "modflowtest",
            "namefile_ext": 'nam',
            "version": "mf2005",
            "exe_name": "mf2005.exe",
            "structured": True,
            "listunit": 2,
            "model_ws": '.',
            "external_path": None,
            "verbose": False
        }
        return default