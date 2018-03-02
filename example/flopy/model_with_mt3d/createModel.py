import os
import sys
import json
import numpy as np
import flopy

"""
TDS:
    - injected water - 150 mg/l
    - ambient water - 1900 mg/l
    - maximum permissible - 300 mg/l

Aquifer thickness (b) (m) 52
Hydraulic conductivity (K) (m/d) 2.5
Transmissivity (T ) (m2/d) 130
Anisotropy ratio (x:y) 1.0
Storage coefficient (S) 2x10-4
Porosity (n) (m3/m3) 0.25
Longitudinal dispersivity (αl ) (m) 5.0
Transverse / longitudinal dispersivity ratio 0.1
Molecular diffusivity (Dm) (m2/s) 10-9
Injection and recovery rates (Qinj/rec) (m3/d) 2160
Regional hydraulic gradient (∂h/∂x) 0.0015
Period of injection (d) Vinj / x.Qinj
Period of recovery (d) Vrec / x.Qrec
"""

nlay, nrow, ncol = 1, 180, 180
nper = 20
perlen = [30]*int(nper)
nstp = [1]*int(nper)

ibound = np.ones((nlay,nrow,ncol), dtype=np.int)

botm = -52.
top = 0.
hk = 2.5
ss = 0.0002
sy = 0.1


half_of_grid = np.hstack((
    np.ones(4)*1000,
    np.ones(2)*300,
    np.ones(84)*5
    ))
delr = np.hstack((half_of_grid, np.flipud(half_of_grid)))
delc = np.hstack((half_of_grid, np.flipud(half_of_grid)))
model_ws = '.'
mf_modelname = 'mf'
mt_modelname = 'mt'

mf = flopy.modflow.Modflow(mf_modelname, model_ws=model_ws, exe_name='mf2005')
dis = flopy.modflow.ModflowDis(mf, nlay=nlay, nrow=nrow, ncol=ncol, nstp=nstp,
                               perlen=perlen, nper=nper, botm=botm, top=top,
                               steady=False, delr=delr, delc=delc)
bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=top)
lpf = flopy.modflow.ModflowLpf(mf, hk=hk, vka=hk, ss=ss, sy=sy)
oc = flopy.modflow.ModflowOc(mf)
pcg = flopy.modflow.ModflowPcg(mf)
lmt = flopy.modflow.ModflowLmt(mf, output_file_name='mt3d_link.ftl',
                               output_file_format='unformatted', output_file_header='extended')

itype = flopy.mt3d.Mt3dSsm.itype_dict()

ssm_data = {}
chd_data = {}
wel_data = {}
for j in range(nper):
    chd_data[j] = []
    ssm_data[j] = []
    wel_data[j] = []

for i in range(nrow):
    for j in range(nper):
        chd_data[j].append((0, i, 0, -7.5, -7.5))
        chd_data[j].append((0, i, ncol-1, 7.5, 7.5))
        ssm_data[j].append((0, i, 0, 1.9, itype['CHD']))
        ssm_data[j].append((0, i, ncol-1, 1.9, itype['CHD']))

chd = flopy.modflow.ModflowChd(mf, stress_period_data=chd_data)

wel_data[0].append((0,90,90, 1595.056964))
wel_data[1].append((0,90,90, 991.9266457))
wel_data[2].append((0,90,90, 1993.937601))
wel_data[3].append((0,90,90, 1967.883056))
wel_data[4].append((0,90,90, -1305.711978))
wel_data[5].append((0,90,90, 1887.980698))
wel_data[6].append((0,90,90, 1921.541385))
wel_data[7].append((0,90,90, -1874.250115))
wel_data[8].append((0,90,90, 1362.413117))
wel_data[9].append((0,90,90, -1763.830609))
wel_data[10].append((0,90,90,-1854.139098))
wel_data[11].append((0,90,90, 1216.258828))
wel_data[12].append((0,90,90, 1993.552115))
wel_data[13].append((0,90,90, -2095.814896))
wel_data[14].append((0,90,90, -1330.091235))
wel_data[15].append((0,90,90, -805.7504521))
wel_data[16].append((0,90,90, -298.2915037))
wel_data[17].append((0,90,90, 2145.025514))
wel_data[18].append((0,90,90, -1667.941155))
wel_data[19].append((0,90,90, -1667.941155))

wel = flopy.modflow.ModflowWel(mf, stress_period_data=wel_data)

for i in range(nper):
    ssm_data[i].append((0, 90, 90, 0.15, itype['WEL']))

mt = flopy.mt3d.Mt3dms(modflowmodel=mf, modelname=mt_modelname, model_ws=model_ws,
                       ftlfilename='mt3d_link.ftl', exe_name='mt3dusgs')

btn = flopy.mt3d.Mt3dBtn(mt, sconc=1.9, ncomp=1, mcomp=1, dt0=30, nprs=-1)
adv = flopy.mt3d.Mt3dAdv(mt, mixelm=0)
dsp = flopy.mt3d.Mt3dDsp(mt, al=5., trpt=0.1, dmcoef=1e-9)
ssm = flopy.mt3d.Mt3dSsm(mt, stress_period_data=ssm_data)
gcg = flopy.mt3d.Mt3dGcg(mt, iter1=100)


mf.write_input()
mf.run_model()
mt.write_input()
mt.run_model()

# Make json

model_input = {
    "author": "Aybulat F",
    "project": "Test model with Mt3d",
    "type": "flopy_calculation",
    "version": "3.2.6",
    "calculation_id": "calculation_id",
    "write_input": True,
    "run_model": True,
    "data": {
        "mf": {
            "run_model": True,
            "write_input": True,
            "packages": ["mf", "dis", "lpf", "bas", "chd", "wel", "oc", "pcg", "lmt"],
            "mf": {
                "modelname": mf_modelname,
                "exe_name": "mf2005",
                "model_ws": ".",
                "version": "mf2005"
            },
            "dis": {
                "nlay": nlay,
                "nrow": nrow,
                "ncol": ncol,
                "nper": nper,
                "delr": delr.tolist(),
                "delc": delc.tolist(),
                "top": top,
                "botm": botm,
                "perlen": perlen,
                "nstp": nstp,
                "steady": False
            },
            "lpf": {
                "hk": hk,
                "vka": hk,
                "ss": ss,
                "sy": sy
            },
            "bas": {
                "ibound": ibound.tolist(),
                "strt": top
            },
            "chd": {
                "stress_period_data": {str(k): list(v) for k, v in chd_data.items()}
            },
            "wel": {
                "stress_period_data": {str(k): list(v) for k, v in wel_data.items()}
            },
            "oc": {},
            "pcg": {},
            "lmt": {
                "output_file_name": 'mt3d_link.ftl',
                "output_file_format": 'unformatted',
                "output_file_header": 'extended'
            }
        },
        "mt": {
            "run_model": True,
            "write_input": True,
            "packages": ["mt", "btn", "adv", "dsp", "gcg", "ssm"],
            "mt": {
                "modelname": mt_modelname,
                "exe_name": "mt3dusgs",
                "model_ws": ".",
                "ftlfilename": "mt3d_link.ftl"
            },
            "btn": {
                "sconc": 1.9,
                "ncomp": 1,
                "mcomp": 1,
                "dt0": 30,
                "nprs": -1
            },
            "adv": {
                "mixelm": 0
            },
            "dsp": {
                "al": 5,
                "trpt": 0.1,
                "dmcoef": 1e-9
            },
            "gcg": {
                "iter1": 100
            },
            "ssm": {
                "stress_period_data": {str(k): list(v) for k, v in ssm_data.items()}
            }
        }
    }
}

with open('model_input.json', 'w') as f:
     json.dump(model_input, f)
