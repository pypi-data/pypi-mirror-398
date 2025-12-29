# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 10:51:01 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""

import carbatpy as cb
import numpy as np
DEFAULTS = cb.CB_DEFAULTS
_THERMO_STRING = DEFAULTS["Fluid_Defaults"]['THERMO_STRING']

# careful density not volume
_THERMO_TREND = request = DEFAULTS["Fluid_Defaults"]['THERMO_TREND']
_TRANS_STRING = DEFAULTS["Fluid_Defaults"]['TRANS_STRING']
_TRANS_TREND = DEFAULTS["Fluid_Defaults"]['TRANS_TREND']
_TRANS_TREND_MIX = DEFAULTS["Fluid_Defaults"]['TRANS_TREND_MIX']
TREND = DEFAULTS['Fluid_Defaults']['TREND']
if TREND["TREND_INSTALLED"]:
    trend_dll = TREND["TREND_DLL"]
    trend_path = TREND["TREND_PATH"]
try:
    import fluid as tr_fl  # TREND fluids

except ImportError as e:
    print(f"Import error for 'fluid': {e}")
import time
P_ACT = 1e5
T_ACT = 370
FLUID = "CO2 * Butane"
comp = [.5, .5]
print("\n------------\n")
#Trend: --------------------------------------
my_dict = {"Input": "TP",
'calctype': "H",
'fluids': FLUID,
"moles": comp,
"eos_ind": [1, 1],
'mix_ind': 1,
'path': trend_path,
'unit': 'specific',
'dll_path': trend_dll}
flm_trend = cb.FluidModel(FLUID, props="TREND", args=my_dict)
my_tr_fl = cb.Fluid(flm_trend, comp)
state_trend = my_tr_fl.set_state([T_ACT, P_ACT], "TP", verbose=True)
print("\n", state_trend)
state_tr_trans = my_tr_fl.set_state([T_ACT, P_ACT], "TP", verbose=True)
print("\n", state_tr_trans)