import os
import flopy.utils.binaryfile as bf


class ReadDrawdown:

    _filename = None

    def __init__(self, workspace):
        for file in os.listdir(workspace):
            if file.endswith(".ddn"):
                self._filename = os.path.join(workspace, file)
        pass

    def read_times(self):
        if not self._filename:
            return []

        heads = bf.HeadFile(filename=self._filename, text='drawdown', precision='single')
        return heads.get_times()

    def read_layer(self, totim, layer):
        if not self._filename:
            return []

        heads = bf.HeadFile(filename=self._filename, text='drawdown', precision='single')
        return heads.get_data(totim=totim, mflay=layer)

    def read_ts(self, layer, row, column):
        if not self._filename:
            return []

        heads = bf.HeadFile(filename=self._filename, text='drawdown', precision='single')
        return heads.get_ts(idx=(layer, row, column))
