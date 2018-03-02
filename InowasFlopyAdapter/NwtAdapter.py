import flopy.modflow as mf


class NwtAdapter:

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
        return mf.ModflowNwt(
            _mf,
            headtol=content['headtol'],
            fluxtol=content['fluxtol'],
            maxiterout=content['maxiterout'],
            thickfact=content['thickfact'],
            linmeth=content['linmeth'],
            iprnwt=content['iprnwt'],
            ibotav=content['ibotavg'],
            options=content['options'],
            Continue=content['continue'],
            dbdtheta=content['dbdtheta'],
            dbdkappa=content['dbdkappa'],
            dbdgamma=content['dbdgamma'],
            momfact=content['momfact'],
            backflag=content['backflag'],
            maxbackiter=content['maxbackiter'],
            backtol=content['backtol'],
            backreduce=content['backreduce'],
            maxitinner=content['maxitinner'],
            ilumethod=content['ilumethod'],
            levfill=content['levfill'],
            stoptol=content['stoptol'],
            msdr=content['msdr'],
            iacl=content['iacl'],
            norder=content['norder'],
            level=content['level'],
            north=content['north'],
            iredsys=content['iredsys'],
            rrctols=content['rrctols'],
            idroptol=content['idroptol'],
            epsrn=content['epsrn'],
            hclosexmd=content['hclosexmd'],
            mxiterxmd=content['mxiterxmd'],
            extension=content['extension'],
            unitnumber=content['unitnumber']
        )

    @staticmethod
    def default():
        default = {
            "headtol": 1E-2,
            "fluxtol": 500,
            "maxiterout": 100,
            "thickfact": 1E-5,
            "linmeth": 1,
            "iprnwt": 0,
            "ibotavg": 0,
            "options": 'COMPLEX',
            "continue": False,
            "dbdtheta": 0.4,
            "dbdkappa": 1.e-5,
            "dbdgamma": 0.,
            "momfact": 0.1,
            "backflag": 1,
            "maxbackiter": 50,
            "backtol": 1.1,
            "backreduce": 0.70,
            "maxitinner": 50,
            "ilumethod": 2,
            "levfill": 5,
            "stoptol": 1.e-10,
            "msdr": 15,
            "iacl": 2,
            "norder": 1,
            "level": 5,
            "north": 7,
            "iredsys": 0,
            "rrctols": 0.0,
            "idroptol": 1,
            "epsrn": 1.e-4,
            "hclosexmd": 1e-4,
            "mxiterxmd": 50,
            "extension": 'nwt',
            "unitnumber": 32
        }

        return default

    @staticmethod
    def read_package(package):
        content = {
            "fluxtol": package.fluxtol,
            "maxiterout": package.maxiterout,
            "thickfact": package.thickfact,
            "linmeth": package.linmeth,
            "iprnwt": package.iprnwt,
            "ibotavg": package.ibotavg,
            "options": package.options,
            "continue": package.continue111,
            "dbdtheta": package.dbdtheta,
            "dbdkappa": package.dbdkappa,
            "dbdgamma": package.dbdgamma,
            "momfact": package.momfact,
            "backflag": package.backflag,
            "maxbackiter": package.maxbackiter,
            "backtol": package.backtol,
            "backreduce": package.backreduce,
            "maxitinner": package.maxitinner,
            "ilumethod": package.ilumethod,
            "levfill": package.levfill,
            "stoptol": package.stoptol,
            "msdr": package.msdr,
            "iacl": package.iacl,
            "norder": package.norder,
            "level": package.level,
            "north": package.north,
            "iredsys": package.iredsys,
            "rrctols": package.rrctols,
            "idroptol": package.idroptol,
            "epsrn": package.epsrn,
            "hclosexmd": package.hclosexmd,
            "mxiterxmd": package.mxiterxmd,
            "extension": package.extension,
            "unitnumber": package.unitnumber
        }
        return content
