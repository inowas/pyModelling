"""
This module is an intermediate layer between flopy version 3.2
and the inowas-modflow-configuration format.

Author: Ralf Junghanns
EMail: ralf.junghanns@gmail.com
"""

from .BasAdapter import BasAdapter
from .ChdAdapter import ChdAdapter
from .DisAdapter import DisAdapter
from .GhbAdapter import GhbAdapter
from .LpfAdapter import LpfAdapter
from .MfAdapter import MfAdapter
from .OcAdapter import OcAdapter
from .PcgAdapter import PcgAdapter
from .RchAdapter import RchAdapter
from .RivAdapter import RivAdapter
from .ReadBudget import ReadBudget
from .ReadDrawdown import ReadDrawdown
from .ReadHead import ReadHead
from .UpwAdapter import UpwAdapter
from .WelAdapter import WelAdapter


class InowasFlopyCalculationAdapter:
    """The Flopy Class"""

    _version = None
    _data = None
    _packages = []
    _packageContent = {}
    _uuid = None

    _mf = None

    def __init__(self, version, data, uuid):
        self._data = data
        self._packages = data.get("packages")
        self._version = version
        self._uuid = uuid
        self.read_packages()
        self.create_model()

        if data.get("write_input"):
            self.write_input_model()

        if data.get("run_model"):
            self.run_model()
        pass

    def read_packages(self):
        for package in self._packages:
            print('Read Flopy Package: %s' % package)
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
            self._mf = MfAdapter(content).get_package()
        if name == 'dis':
            DisAdapter(content).get_package(self._mf)
        if name == 'bas':
            BasAdapter(content).get_package(self._mf)
        if name == 'lpf':
            LpfAdapter(content).get_package(self._mf)
        if name == 'upw':
            UpwAdapter(content).get_package(self._mf)
        if name == 'pcg':
            PcgAdapter(content).get_package(self._mf)
        if name == 'oc':
            OcAdapter(content).get_package(self._mf)
        if name == 'riv':
            RivAdapter(content).get_package(self._mf)
        if name == 'wel':
            WelAdapter(content).get_package(self._mf)
        if name == 'rch':
            RchAdapter(content).get_package(self._mf)
        if name == 'chd':
            ChdAdapter(content).get_package(self._mf)
        if name == 'ghb':
            GhbAdapter(content).get_package(self._mf)

    def response(self):
        heads = ReadHead(self._packageContent['mf']['model_ws'])
        drawdowns = ReadDrawdown(self._packageContent['mf']['model_ws'])
        budgets = ReadBudget(self._packageContent['mf']['model_ws'])

        response = {}
        response['status_code'] = "200"
        response['id'] = self._uuid
        response['heads'] = heads.read_times()
        response['drawdowns'] = drawdowns.read_times()
        response['budgets'] = budgets.read_times()
        response['number_of_layers'] = heads.read_number_of_layers()

        return response
