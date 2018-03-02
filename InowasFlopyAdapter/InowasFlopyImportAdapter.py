"""
This module is an intermediate layer between flopy version 3.2
and the inowas-modflow-configuration format.

Serialize Modflow and MT3D model into JSON format
"""
import os
import flopy.modflow
import flopy.mt3d
from .BasAdapter import BasAdapter
from .ChdAdapter import ChdAdapter
from .DisAdapter import DisAdapter
from .GhbAdapter import GhbAdapter
from .LpfAdapter import LpfAdapter
from .MfAdapter import MfAdapter
from .NwtAdapter import NwtAdapter
from .OcAdapter import OcAdapter
from .PcgAdapter import PcgAdapter
from .RchAdapter import RchAdapter
from .RivAdapter import RivAdapter
from .ReadBudget import ReadBudget
from .ReadDrawdown import ReadDrawdown
from .ReadHead import ReadHead
from .UpwAdapter import UpwAdapter
from .WelAdapter import WelAdapter


class InowasFlopyImportAdapter:
    """The Flopy Class"""

    def __init__(self, model_ws, mf_name=None, mt_name=None):
        self._report = ''
        self.data = {}
        self.packages = []
        self.mf_model, self.mt_model = None, None

        if mf_name is not None:
            self.data["mf"] = {}
            self.mf_model = flopy.modflow.Modflow.load(os.path.join(model_ws, mf_name))
            self.packages += self.mf_model.get_package_list() + "mf"
        if mt_name is not None:
            self.data["mt"] = {}
            self.mt_model = flopy.mt3d.Mt3dms.load(os.path.join(model_ws, mt_name))
            self.packages += self.mt_model.get_package_list() + "mt"

    def serialize(self):
        for package_name in self.packages:
            self.read_packages(name=package_name)

    def read_packages(self, name):
        #Modlfow packages
        if name == 'mf':
            self.data["mf"]["mf"] = MfAdapter(data=None).read_package(self.mf_model)
        if name == 'dis':
            self.data["mf"]["dis"] = DisAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'bas':
            self.data["mf"]["bas"] = BasAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'lpf':
            self.data["mf"]["lpf"] = LpfAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'upw':
            self.data["mf"]["upw"] = UpwAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'pcg':
            self.data["mf"]["pcg"] = PcgAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'nwt':
            self.data["mf"]["nwt"] = NwtAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'oc':
            self.data["mf"]["oc"] = OcAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'riv':
            self.data["mf"]["riv"] = RivAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'wel':
            self.data["mf"]["wel"] = WelAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'rch':
            self.data["mf"]["rch"] = RchAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'chd':
            self.data["mf"]["chd"] = ChdAdapter(data=None).read_package(self.mf_model.get_package(name))
        if name == 'ghb':
            self.data["mf"]["ghb"] = GhbAdapter(data=None).read_package(self.mf_model.get_package(name))
        
        #MT3D packages 
        if name == 'mt':
            self.data["mt"]["mt"] = MtAdapter(data=None).read_package(self.mt_model)


    def response_message(self):
        return self._report
