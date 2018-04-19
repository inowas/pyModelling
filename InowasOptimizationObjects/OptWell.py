"""
Optimized model objects - Well
"""

import numpy as np
from collections import OrderedDict


class OptWell(object):
    """Well used in optimization process"""
    def __init__(self, data):
        self.idx = data['id']
        self.variables_map = OrderedDict()
        self.flux_mask = None
        self.concentration_mask = None
        self.flux_multiplier = 1
        self.conc_multiplier = 1
        self.position_multiplier = 1

        self.map_variables(data)

    def map_variables(self, data):
        """
        Returns ordered variables dict where non None values are fixed ones
        Example: {
            ('position', 'lay'): 0,
            ('position', 'row'): None,
            ('position', 'col'): None,
            ('flux', 0): None, ---- here 0 is period
            ('concentration', 0, 0): 0 ---- here 0, 0 is period, componenet
        }
        """
        flux_length = 0
        concentration_length = 0
        concentration_width = 0

        for key, value in data.items():
            if key == 'position':
                for k, v in value.items():
                    if k != 'multiplier':
                        if v[0] == v[1]:
                            self.variables_map[(key, k)] = v[0]
                        else:
                            self.variables_map[(key, k)] = None
                    else:
                        self.position_multiplier = int(v)

            if key == 'flux':
                for k, v in value.items():
                    if k != 'multiplier':
                        if v[0] == v[1]:
                            self.variables_map[(key, k)] = v[0]
                        else:
                            self.variables_map[(key, k)] = None
                        flux_length += 1
                    else:
                        self.flux_multiplier = int(v)

            if key == 'concentration':
                for k, v in value.items():
                    if k != 'multiplier':
                        for idx, i in enumerate(v):
                            if i[0] == i[1]:
                                self.variables_map[(key, k, idx)] = i[0]
                            else:
                                self.variables_map[(key, k, idx)] = None
                        concentration_length += 1
                        concentration_width = len(v)
                    else:
                        self.conc_multiplier = int(v)
            
            self.flux_mask = np.zeros((flux_length))
            self.concentration_mask = np.zeros((concentration_length, concentration_width))

    def update_packages(self, data, individual):
        """Add candidate well data to SPD """
        lay, row, col, fluxes, concentrations = self.format_individual(
            self.variables_map, individual, self.flux_mask, self.concentration_mask
        )

        if fluxes is not None:
            try:
                spd = data["mf"]["wel"]["stress_period_data"]
            except KeyError:
                spd = {}

            fluxes = fluxes * self.flux_multiplier

            data["mf"]["wel"]["stress_period_data"] = self.update_wel_spd(
                lay, row, col, 
                fluxes, spd
            )
        
        if concentrations is not None:
            try:
                spd = data["mt"]["ssm"]["stress_period_data"]
            except KeyError:
                spd = {}

            concentrations = concentrations * self.conc_multiplier

            data["mt"]["ssm"]["stress_period_data"] = self.update_ssm_spd(
                lay, row, col, 
                concentrations, spd
            )

        return data

    def update_wel_spd(self, lay, row, col, fluxes, spd):
        """Updates WEL SPD"""
        
        for idx, val in enumerate(fluxes):
            if not idx in spd:
                spd[idx] = []
           
            spd[idx].append([lay, row, col, val])

        return spd

    def update_ssm_spd(self, lay, row, col, concentrations, spd):
        """Updates SSM SPD"""

        dummy_concentration_value = 1.
        well_itype = 2
        
        for idx, val in enumerate(concentrations):
            if len(val) > 1:
                record = [lay, row, col, dummy_concentration_value, well_itype]
                for v in val:
                    record.append(v)
            else:
                record = [lay, row, col, val[0], well_itype]

            if not idx in spd:
                spd[idx] = []
            spd[idx].append(record)

        return spd

    @staticmethod
    def format_individual(variables_map, individual, flux_mask, concentration_mask):
        """Returns input values converted from an individual"""
        
        variables = {}
        fluxes = None
        concentrations = None

        #Get variable either from individual or from variables map
        i = 0
        for var, val in variables_map.items():
            if val is None:
                variables[var] = individual[i]
                i += 1
            else:
                variables[var] = val
        #Format variables
        for k, v in variables.items():
            if k == ('position', 'lay'):
                lay = v
            elif k == ('position', 'row'):
                row = v
            elif k == ('position', 'col'):
                col = v
            elif k[0] == 'flux':
                if fluxes is None:
                    fluxes = np.zeros(flux_mask.shape)
                flux_ts = int(k[1])
                fluxes[flux_ts] = v
            elif k[0] == 'concentration':
                if concentrations is None:
                    concentrations = np.zeros(concentration_mask.shape)
                concentraion_ts = int(k[1])
                concentraion_comp = int(k[2])
                concentrations[concentraion_ts][concentraion_comp] = v

        return lay, row, col, fluxes, concentrations
