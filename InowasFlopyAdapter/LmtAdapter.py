import flopy.modflow as mf


class LmtAdapter:

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
        return mf.ModflowLmt(
                _mf,
                **content
            )

    @staticmethod
    def default():
           
        default = {
            "output_file_name": 'mt3d_link.ftl',
            "output_file_unit": 54,
            "output_file_header": 'extended',
            "output_file_format": 'unformatted',
            "extension": 'lmt6',
            "package_flows": [],
            "unitnumber": None,
            "filenames": None
        }

        return default
