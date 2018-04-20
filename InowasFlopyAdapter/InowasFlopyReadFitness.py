"""
Calculation of objective values of a model 

Author: Aybulat Fatkhutdinov
"""

import os
import math
import numpy as np
import flopy


class InowasFlopyReadFitness:
    """Calculation of objective values of a model """

    def __init__(self, optimization_data, flopy_adapter):

        self.optimization_data = optimization_data

        self.dis_package = flopy_adapter._mf.get_package('DIS')
        self.model_ws = flopy_adapter._mf.model_ws
        self.model_name = flopy_adapter._mf.model.nam

        objectives_values = self.read_objectives()
        constrains_exceeded = self.check_constrains()

        if True in constrains_exceeded or None in objectives_values:
            self.fitness = [obj["penalty_value"] for obj in optimization_data["objectives"]]
        else:
            self.fitness = objectives_values


    def get_fitness(self):

        return self.fitness

    def read_objectives(self):
        "Returnes fitnes list"
        fitness = []

        for objective in self.optimization_data["objectives"]:

            if objective["type"] is not "flux" and objective["type"] is not "distance":
                mask = self.make_mask(
                    objective["location"], self.optimization_data["temp_objects"], self.dis_package
                )

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

            elif objective["type"] == "flux":
                fitness.append(
                    self.read_flux(objective, self.optimization_data["temp_objects"])
                )
            
            elif objective["type"] == "input_concentrations":
                fitness.append(
                    self.read_input_concentration(objective, self.optimization_data["temp_objects"])
                )
            
            elif objective["type"] == "flux":
                fitness.append(
                    self.read_distance(objective, self.optimization_data["temp_objects"])
                )

        return fitness
    
    def check_constrains(self):
        """Returns a list of penalty values"""
        constrains_exceeded = []

        for constrain in self.optimization_data["constrains"]:
            mask = self.make_mask(
                constrain["location"], self.optimization_data["temp_objects"], self.dis_package    
            )

            if constrain["type"] == 'head':
                value = self.read_head(
                    constrain, mask, self.model_ws, self.model_name
                )
   
            elif constrain["type"] == 'concentration':
                value = self.read_concentration(
                    constrain, mask, self.model_ws, self.model_name
                )
            
            elif constrain["type"] == "flux":
                value = self.read_flux(
                    constrain, self.optimization_data["temp_objects"]
                )
            
            elif constrain["type"] == "input_concentrations":
                value = self.read_input_concentration(
                    constrain, self.optimization_data["temp_objects"]
                )
            
            elif constrain["type"] == "flux":
                value = self.read_distance(
                    constrain, self.optimization_data["temp_objects"]
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
    
    @staticmethod
    def read_flux(data, temp_objects):
        "Reads wel fluxes"
        fluxes = np.array([])
        try:
            for obj in data["location"]["objects"]:
                fluxes = np.hstack((fluxes, temp_objects[obj]["fluxes"]))
        except KeyError:
            print("WARNING! Objective location of type Flux has to be an Object!")
            return None

        if data["method"] == 'mean':
            flux = np.nanmean(fluxes)
        elif data["method"] == 'max':
            flux = np.max(fluxes)
        elif data["method"] == 'min':
            flux = np.min(fluxes)

        return flux
    
    @staticmethod
    def read_input_concentration(data, temp_objects):
        input_concentrations = np.array([])

        try:
            component = data["component"]
        except KeyError:
            print("WARNING! Concentration component for the Objective of type input_concentrations is not defined!")
            return None
        try:
            for obj in data["location"]["objects"]:
                input_concentrations = np.hstack(
                    (input_concentrations, 
                     np.array(temp_objects[obj]["input_concentrations"])[:,component])
                )
        except KeyError:
            print("WARNING! Objective location of type Input_concentrations has to be an Object!")
            return None

        if data["method"] == 'mean':
            input_concentrations = np.nanmean(input_concentrations)
        elif data["method"] == 'max':
            input_concentrations = np.max(input_concentrations)
        elif data["method"] == 'min':
            input_concentrations = np.min(input_concentrations)

        return input_concentrations
    
    @staticmethod
    def read_distance(data, temp_objects):
        """Returns distance between two groups of objects"""
        location_1 = data["location_1"]
        location_2 = data["location_2"]
        
        objects_1 = None
        objects_2 = None

        if location_1['type'] == 'object':
            objects_1 = [
                obj for id_, obj in temp_objects.items() if id_ in location_1['objects_ids']
            ]

        if location_2['type'] == 'object':
            objects_2 =[
                obj for id_, obj in temp_objects.items() if id_ in location_2['objects_ids']
            ]
        
        distances = []
        if objects_1 is not None:
            for obj_1 in objects_1:
                if objects_2 is not None:
                    for obj_2 in objects_2:
                        dx = float(abs(obj_2["col"] - obj_1["col"]))
                        dy = float(abs(obj_2["row"] - obj_1["row"]))
                        dz = float(abs(obj_2["lay"] - obj_1["lay"]))
                        distances.append(math.sqrt((dx**2) + (dy**2) + (dz**2)))
                else:
                    dx = float(abs(location_2['lay_row_col'][2] - obj_1["col"]))
                    dy = float(abs(location_2['lay_row_col'][1] - obj_1["row"]))
                    dz = float(abs(location_2['lay_row_col'][0] - obj_1["lay"]))
                    distances.append(math.sqrt((dx**2) + (dy**2) + (dz**2)))
        else:
            if objects_2 is not None:
                for obj_2 in objects_2:
                    dx = float(abs(obj_2["col"] - location_1['lay_row_col'][2]))
                    dy = float(abs(obj_2["row"] - location_1['lay_row_col'][1]))
                    dz = float(abs(obj_2["lay"] - location_1['lay_row_col'][0]))
                    distances.append(math.sqrt((dx**2) + (dy**2) + (dz**2)))
            else:
                dx = float(abs(location_2['lay_row_col'][2]-location_1['lay_row_col'][2]))
                dy = float(abs(location_2['lay_row_col'][1]-location_1['lay_row_col'][1]))
                dz = float(abs(location_2['lay_row_col'][0]-location_1['lay_row_col'][0]))
                distances.append(math.sqrt((dx**2) + (dy**2) + (dz**2)))

        distances = np.array(distances)

        if data["method"] == 'mean':
            distance = np.nanmean(distances)
        elif data["method"] == 'max':
            distance = np.max(distances)
        elif data["method"] == 'min':
            distance = np.min(distances)
        
        return distance

    @staticmethod
    def make_mask(location, temp_objects, dis_package):
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

        elif location["type"] == 'object':
            lays = []
            rows = []
            cols = []
            for obj in location["objects"]:
                lays.append(temp_objects[obj]["lay"])
                rows.append(temp_objects[obj]["row"])
                cols.append(temp_objects[obj]["col"])

            mask = np.zeros((nstp_flat, nlay, nrow, ncol), dtype=bool)
            mask[:,lays,rows,cols] = True
        
        return mask