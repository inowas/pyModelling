#! /usr/env python

from sklearn.gaussian_process import GaussianProcess
import numpy as np


class Mean:

    _nX = 0
    _nY = 0
    _values = []

    def __init__(self, data):

        if 'grid_size' in data:
            grid_size = data['grid_size']

            if 'n_x' in grid_size:
                self._nX = grid_size['n_x']

            if 'n_y' in grid_size:
                self._nY = grid_size['n_y']

        for point in data['point_values']:
            if 'value' in point:
                self._values.append(point['value'])

    def calculate(self):

        try:
            result = self.mean(self._nX, self._nY, self._values)
        except:
            result = False

        return result

    @staticmethod
    def mean(nx, ny, values):
        mean_value = np.mean(values)
        grid = mean_value * np.ones((ny, nx))
        return grid
