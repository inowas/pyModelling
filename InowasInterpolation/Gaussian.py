#! /usr/env python

from sklearn.gaussian_process import GaussianProcess
import numpy as np


class Gaussian:

    _xMin = 0.0
    _xMax = 0.0
    _yMin = 0.0
    _yMax = 0.0
    _nX = 0
    _nY = 0
    _dX = 0.0
    _dY = 0.0
    _X = []
    _Y = []

    def __init__(self, data):

        if 'bounding_box' in data:
            bounding_box = data['bounding_box']

            if 'x_min' in bounding_box:
                self._xMin = float(bounding_box['x_min'])

            if 'x_max' in bounding_box:
                self._xMax = float(bounding_box['x_max'])

            if 'y_min' in bounding_box:
                self._yMin = float(bounding_box['y_min'])

            if 'y_max' in bounding_box:
                self._yMax = float(bounding_box['y_max'])

        if 'grid_size' in data:
            grid_size = data['grid_size']

            if 'n_x' in grid_size:
                self._nX = grid_size['n_x']

            if 'n_y' in grid_size:
                self._nY = grid_size['n_y']

        self._dX = (self._xMax - self._xMin) / self._nX
        self._dY = (self._yMax - self._yMin) / self._nY

        self._X = []
        self._Y = []

        for point in data['point_values']:
            if 'x' in point and 'y' in point:
                self._X.append([point['x'], point['y']])

            if 'value' in point:
                self._Y.append(point['value'])

    def calculate(self):

        try:
            result = self.gaussian_process(self._nX, self._nY, self._X, self._Y, self._xMin, self._yMin, self._dX, self._dY)
        except:
            result = False

        return result

    @staticmethod
    def gaussian_process(nx, ny, x, y, x_min, y_min, dx, dy):
        """
        Gausian process method. To replace kriging.
        Description:
        http://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcess.html#sklearn.gaussian_process.GaussianProcess.predict
        The scikit learn python library should be installed
        Should be tested
        """

        # Prediction is very sensitive to the parameters below, please use with care!
        gp = GaussianProcess(regr='quadratic', corr='cubic', theta0=0.1, thetaL=.001, thetaU=1., nugget=0.01)
        gp.fit(x, y)

        x_grid_x = np.linspace(x_min, x_min + dx * nx, nx)
        x_grid_y = np.linspace(y_min, y_min + dy * ny, ny)
        xv, yv = np.meshgrid(x_grid_x, x_grid_y)
        x_grid = np.dstack((xv.flatten(), yv.flatten()))[0]
        grid = np.reshape(gp.predict(x_grid, eval_MSE=False, batch_size=None), (ny, nx))

        return grid
