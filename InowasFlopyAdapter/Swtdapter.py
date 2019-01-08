import flopy.seawat as swt


class SwtAdapater:
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
        return swt.Seawat(
            **content
        )

    @staticmethod
    def default():
        default = {
            "modelname": "swttest",
            "namefile_ext": 'nam',
            "modflowmodel": None,
            "mt3dmodel": None,
            "version": "seawat",
            "exe_name": "swt_v4.exe",
            "structured": True,
            "listunit": 2,
            "model_ws": '.',
            "external_path": None,
            "verbose": False,
            "load": True,
            "silent": 0
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "modelname": package.modelname,#None
            "namefile_ext": package.namefile_ext,
            "modflowmodel": package.modflowmodel,
            "mt3dmodel": package.mt3dmodel,
            "version": package.version,
            "exe_name": package.exe_name,
            "structured": package.structured,
            "listunit": package.listunit,
            "model_ws": package.model_ws,
            "external_path": package.external_path,
            "verbose": package.verbose,
            "load": package.load,
            "silent": package.silent
        }
        return content
