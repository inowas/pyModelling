"""
Calculation of objective values of a model 

Author: Aybulat Fatkhutdinov
"""

import os
import numpy as np
import flopy

# from .InowasFitnessTools import Objective
# from .InowasFitnessTools import Constrain



class InowasFlopyReadFitness:
    """Calculation of objective values of a model """

    def __init__(self, fitness_data, flopy_adapter):

        self.dis_package = flopy_adapter._mf.get_package('DIS')
        self.model_ws = flopy_adapter._mf.model_ws
        self.model_name = flopy_adapter._mf.model.nam

        objectives_values = self.read_objectives(fitness_data["objectives"])
        constrains_exceeded = self.check_constrains(fitness_data["constrains"])

        if True in constrains_exceeded or None in objectives_values:
            self.fitness = [obj["penalty_value"] for obj in fitness_data["objectives"]]
        else:
            self.fitness = objectives_values


    def get_fitness(self):

        return self.fitness


        
    
    @staticmethod
    def make_mask(location, dis_package):
        "Returns an array mask of location that has nper,nlay,nrow,ncol dimensions"
        nstp_flat = dis_package.nstp.array.sum()
        nrow = dis_package.nrow
        ncol = dis_package.ncol
        nlay = dis_package.nlay

        if location["type"] == 'bbox':
            try:
                per_min = location['per_min']
            except KeyError:
                per_min = 0

            try:
                per_max = location['per_max']
            except KeyError:
                per_max = nstp_flat

            try:
                lay_min = location['lay_min']
            except KeyError:
                lay_min = 0

            try:
                lay_max = location['lay_max']
            except KeyError:
                lay_max = nlay

            try:
                col_min = location['col_min']
            except KeyError:
                col_min = 0

            try:
                col_max = location['col_max']
            except KeyError:
                col_max = ncol

            try:
                row_min = location['row_min']
            except KeyError:
                row_min = 0

            try:
                row_max = location['row_max']
            except KeyError:
                row_max = nrow

            if per_min == per_max:
                per_max += 1
            if lay_min == lay_max:
                lay_max += 1
            if row_min == row_max:
                row_max += 1
            if col_min == col_max:
                col_max += 1
        
            mask = np.zeros((nstp_flat, nlay, nrow, ncol), dtype=bool)
            mask[
                per_min:per_max,
                lay_min:lay_max,
                row_min:row_max,
                col_min:col_max
            ] = True

        # elif location["type"] == 'object':
        #     lays = []
        #     rows = []
        #     cols = []
        #     for obj in location["objects"]:
        #         lays.append(obj.lay)
        #         rows.append(obj.row)
        #         cols.append(obj.col)

        #     mask = np.zeros((nstp_flat, nlay, nrow, ncol), dtype=bool)
        #     mask[:,lays,rows,cols] = True
        
        return mask
        

    def read_objectives(self, objectives_data):
        "Returnes fitnes list"
        fitness = []

        for objective in objectives_data:
            mask = self.make_mask(objective["location"], self.dis_package)

            if objective["type"] == "concentration":
                fitness.append(
                    self.read_concentration(
                        objective, mask, self.model_ws, self.model_name
                    )
                )

            elif objective["type"] == "head":
                fitness.append(
                    self.read_head(
                        objective, mask, self.model_ws, self.model_name
                    )
                )

            # elif objective["type"] == "flux":
            #     fitness.append(self.read_flux(objective, mask))

        return fitness
    
    def check_constrains(self, constrains_data):
        """Returns a list of penalty values"""
        constrains_exceeded = []

        for constrain in constrains_data:
            mask = self.make_mask(constrain["location"], self.dis_package)

            if constrain.type == 'head':
                value = self.read_head(
                    constrain, mask, self.model_ws, self.model_name
                )
   
            elif constrain.type == 'concentration':
                value = self.read_concentration(
                    constrain, mask, self.model_ws, self.model_name
                )     
            
            if constrain["operator"] == "less":
                constrains_exceeded.append(
                    True if value > constrain["value"] else False
                )

            elif constrain["operator"] == "more":
                constrains_exceeded.append(
                    True if value < constrain["value"] else False
                )
  

        return constrains_exceeded

    @staticmethod
    def read_head(data, mask, model_ws, model_name):
        "Reads head file"
        try:
            head_file_object = flopy.utils.HeadFile(
                os.path.join(model_ws, model_name) + '.hds')
            head = head_file_object.get_alldata(
                nodata=-9999
                )
            head = head[mask]

            head_file_object.close()

        except:
            print('Head file of the model: '+model_name+' could not be opened')
            return None

        if data["method"] == 'mean':
            head = np.nanmean(head)
        elif data["method"] == 'maximum':
            head = np.max(head)
        elif data["method"] == 'min':
            head = np.min(head)

        return head
    
    @staticmethod
    def read_concentration(data, mask, model_ws, model_name):
        "Reads concentrations file"
        try:
            conc_file_object = flopy.utils.UcnFile(
                os.path.join(model_ws, data["conc_file_name"]))
            conc = conc_file_object.get_alldata(
                nodata=-9999
                )
            conc = conc[mask]

            conc_file_object.close()
        
        except:
            print('Concentrations file of the model: '+model_name+' could not be opened')
            return None

        if data["method"] == 'mean':
            conc = np.nanmean(conc)
        elif data["method"] == 'max':
            conc = np.max(conc)
        elif data["method"] == 'min':
            conc = np.min(conc)

        return conc
    
    
    # def read_flux():


    #     return flux
