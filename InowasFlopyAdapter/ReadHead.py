import os
import flopy.utils.binaryfile as bf


class ReadHead:

    _filename = ""

    def __init__(self, workspace, modelname):
        self._filename = os.path.join(workspace, modelname + '.hds')
        pass

    def read_times(self):
        if not os.path.exists(self._filename):
            return []

        heads = bf.HeadFile(filename=self._filename, precision='single')
        return heads.get_times()

    def read_head(self, totim, layer):
        if not os.path.exists(self._filename):
            return []

        heads = bf.HeadFile(filename=self._filename, precision='single')
        return heads.get_data(totim=totim, mflay=layer)

    def read_ts(self, layer, row, column):
        if not os.path.exists(self._filename):
            return []

        heads = bf.HeadFile(filename=self._filename, precision='single')
        return heads.get_ts(idx=(layer, row, column))
