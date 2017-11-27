import os
import sys
import flopy.modflow as mf
import flopy.utils as fu
import json

workspace = os.path.join('Input')
modelname = 'tuc4010'

scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, '../../../bin')

exe_name = os.path.join(binfolder, sys.platform, 'mfnwt')

ml = mf.Modflow.load(modelname+'.nam', version='mfnwt', exe_name=exe_name, model_ws=workspace, verbose=False)

print(ml)
print(ml.packagelist[3])
