import os
from flopy.utils.mflistfile import MfListBudget


class ReadBudget:

    _filename = None

    def __init__(self, workspace):
        for file in os.listdir(workspace):
            if file.endswith(".list"):
                self._filename = os.path.join(workspace, file)
        pass

    def read_times(self):
        if not self._filename:
            return []
        mf_list = MfListBudget(self._filename)
        return mf_list.get_times()

    def read_cumulative_budget(self, totim):
        if not self._filename:
            return []
        mf_list = MfListBudget(self._filename)
        budget = mf_list.get_data(totim=totim, incremental=False)
        values = {}
        for x in budget:
            param = str(x[2].decode('UTF-8'))
            values[param] = str(x[1])
        return values

    def read_incremental_budget(self, totim):
        if not self._filename:
            return []
        mf_list = MfListBudget(self._filename)
        budget = mf_list.get_data(totim=totim, incremental=True)
        values = {}
        for x in budget:
            param = str(x[2].decode('UTF-8'))
            values[param] = str(x[1])
        return values
