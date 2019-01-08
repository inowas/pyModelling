import flopy.seawat as swt


class VscAdapater:
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
        return swt.SeawatVdf(
            **content
        )

    @staticmethod
    def default():
        default = {
            "mt3dmuflg" = -1,
            "viscmin" = 0.,
            "viscmax" = 0.,
            "viscref" = 8.904e-4,
            "nsmueos" = 0,
            "mutempopt" = 2,
            "mtmuspec" = 1,
            "dmudc" = 1.923e-06,
            "cmuref" = 0.,
            "mtmutempspec" = 1,
            "amucoeff" = None,
            "invisc" = -1,
            "visc" = -1,
            "extension" = 'vsc',
            "unitnumber" = None,
            "filenames" = None,
        }
        return default

    @staticmethod
    def read_package(package):
        content = {
            "mt3dmuflg": package.mt3dmuflg,
            "viscmin": package.viscmin,
            "viscmax": package.viscmax,
            "viscref": package.viscref,
            "nsmueos": package.nsmueos,
            "mutempopt": package.mutempopt,
            "mtmuspec": package.mtmuspec,
            "dmudc": package.dmudc,
            "cmuref": package.cmuref,
            "mtmutempspec": package.mtmutempspec,
            "amucoeff": package.amucoeff,
            "invisc": package.invisc,
            "visc": package.visc,
            "extension": package.extension,
            "unitnumber": package.unitnumber,
            "filenames": package.filenames,
        }
        return content
