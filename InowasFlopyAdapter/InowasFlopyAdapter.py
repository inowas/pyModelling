#! /usr/env python

import flopy.modflow as mf

class InowasFlopyAdapter:
    """The Flopy Class"""

    _version = None
    _data = None
    _packages = []
    _packageContent = {}

    _mf = None

    def __init__(self, version, data):
        self._version = version
        self._data = data
        self._packages = data.get("packages")
        self.read_packages()
        self.create_model()

        if data.get("write_input"):
            self.write_input_model()

        if data.get("run_model"):
            self.run_model()
        pass

    def read_packages(self):
        for package in self._packages:
            print('Create Flopy Package: %s' % package)
            self._packageContent[package] = self._data[package]

    def create_model(self):
        for package in self._packages:
            print('Create Flopy Package: %s' % package)
            self.create_package(package, self._packageContent[package])

    def write_input_model(self):
        print('Write input files')
        self._mf.write_input()

    def run_model(self):
        print('Run the model')
        self._mf.run_model()

    def check_model(self):
        self._mf.check()

    def create_package(self, name, content):
        if name == 'mf':
            self._mf = mf.Modflow(
                modelname=content['modelname'],
                exe_name=content['exe_name'],
                version=content['version'],
                model_ws=content['model_ws']
            )
        if name == 'dis':
            mf.ModflowDis(
                self._mf,
                nlay=content['nlay'],
                nrow=content['nrow'],
                ncol=content['ncol'],
                nper=content['nper'],
                delr=content['delr'],
                delc=content['delc'],
                laycbd=content['laycbd'],
                top=content['top'],
                botm=content['botm'],
                perlen=content['perlen'],
                nstp=content['nstp'],
                tsmult=content['tsmult'],
                steady=content['steady'],
                itmuni=content['itmuni'],
                lenuni=content['lenuni'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                xul=content['xul'],
                yul=content['yul'],
                rotation=content['rotation'],
                proj4_str=content['proj4_str'],
                start_datetime=content['start_datetime']
            )
        if name == 'bas':
            mf.ModflowBas(
                self._mf,
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
        if name == 'lpf':
            mf.ModflowLpf(
                self._mf,
                laytyp=content['laytyp'],
                layavg=content['layavg'],
                chani=content['chani'],
                layvka=content['layvka'],
                laywet=content['laywet'],
                ipakcb=content['ipakcb'],
                hdry=content['hdry'],
                iwdflg=content['iwdflg'],
                wetfct=content['wetfct'],
                iwetit=content['iwetit'],
                ihdwet=content['ihdwet'],
                hk=content['hk'],
                hani=content['hani'],
                vka=content['vka'],
                ss=content['ss'],
                sy=content['sy'],
                vkcb=content['vkcb'],
                wetdry=content['wetdry'],
                storagecoefficient=content['storagecoefficient'],
                constantcv=content['constantcv'],
                thickstrt=content['thickstrt'],
                nocvcorrection=content['nocvcorrection'],
                novfc=content['novfc'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'pcg':
            mf.ModflowPcg(
                self._mf,
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
        if name == 'oc':
            mf.ModflowOc(
                self._mf,
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
        if name == 'riv':
            mf.ModflowRiv(
                self._mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                options=content['options'],
                naux=content['naux']
            )
        if name == 'wel':
            mf.ModflowWel(
                self._mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                options=content['options']
            )
        if name == 'rch':
            mf.ModflowRch(
                self._mf,
                ipakcb=content['ipakcb'],
                nrchop=content['nrchop'],
                rech=content['rech'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'chd':
            mf.ModflowChd(
                self._mf,
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                options=content['options'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

        if name == 'ghb':
            mf.ModflowGhb(
                self._mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                options=content['options'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )


    @staticmethod
    def get_stress_period_data(stress_periods):
        stress_period_data = {}
        for stress_period in stress_periods:
            print(stress_period)
            stress_period_data[stress_period['stressPeriod'], stress_period['timeStep']] = stress_period['type']

        return stress_period_data
