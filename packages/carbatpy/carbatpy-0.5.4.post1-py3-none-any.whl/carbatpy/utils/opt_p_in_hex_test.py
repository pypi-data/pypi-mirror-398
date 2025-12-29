# -*- coding: utf-8 -*-
"""

This script optimizes the pressure of the working fluid in a heat exchanger

the mean temperature difference is minimized, without having a point below
the minimum approach temperature (pinch point).
it works, but is slow.

Created on Tue Jul 23 11:26:13 2024

@author: atakan
"""


import copy
from time import time
# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import minimize, minimize_scalar, Bounds  # root, root_scalar
import matplotlib.pyplot as plt
import carbatpy as cb


FLUID = "Propane * Pentane"  # working fluid
FLS = "Methanol"  # "Water"  # secondary fluid
comp = [.50, 0.5]
flm = cb.fprop.FluidModel(FLUID)
myFluid = cb.fprop.Fluid(flm, comp)

secFlm = cb.fprop.FluidModel(FLS)
secFluid = cb.fprop.Fluid(secFlm, [1.])
D_TEMP_MIN = 5.0

# Condenser, working fluid fixes all, secondary output enthalpy can be varied:
SEC_TEMP_IN = 300.0
SEC_TEMP_OUT_MAX = 370.0
SEC_PRES_IN = 5e5
H_DOT = 1e3
state_sec_out = secFluid.set_state([SEC_TEMP_OUT_MAX, SEC_PRES_IN], "TP")

state_sec_in = secFluid.set_state(
    [SEC_TEMP_IN, SEC_PRES_IN], "TP")  # this is the entering state

# working fluid

TEMP_SAT_VAP = SEC_TEMP_OUT_MAX + D_TEMP_MIN
state_in = myFluid.set_state(
    [TEMP_SAT_VAP, 1.], "TQ")  # find minimum pressure

WF_TEMP_IN = TEMP_SAT_VAP + D_TEMP_MIN
WF_TEMP_OUT = SEC_TEMP_IN + D_TEMP_MIN
state_out = myFluid.set_state([WF_TEMP_OUT, state_in[1]], "TP")

# now plotting can directly be done in pinch_calc 2024-05-24
fig_act, ax_act = plt.subplots(1)
PLOT_INFO = {"fig": fig_act, "ax": ax_act, "what": [2, 0], "col": ["r:", "ko"],
             "label": ["work,c", "sec,c"], "x-shift": [0, 0]}

# a simple way to find an optimal/better pressure level
pressures_good =[]
p_start = state_out[1]

# p_range = np.linspace(p_start*.87, p_start*1.015,11)
# for p_act in p_range:

#     state_in = myFluid.set_state([p_act,
#                                   WF_TEMP_IN],
#                                  "PT")
#     # myFluid.print_state()

#     hex0 = cb.models.components.heat_exchanger_thermo_v2.StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
#                                state_sec_out[2],
#                                d_temp_separation_min=D_TEMP_MIN)
    

#     factor0 = hex0.find_pinch()
#     if hex0.warning ==0:
#         pressures_good.append([p_act, hex0.dt_mean, hex0.warning, hex0.warning_message])
#     print(p_act, hex0.dt_mean, hex0.warning, hex0.warning_message)
# if hex0.warning > 0:
#     print(hex0.warning_message)
# print("useful pressures:\n",pressures_good,"\n\n")    
# hex0 = cb.models.components.heat_exchanger_thermo_v2.StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
#                             state_sec_out[2],
#                             d_temp_separation_min=D_TEMP_MIN)

def to_opt(p_act):
    state_in = myFluid.set_state([p_act,
                                  WF_TEMP_IN],
                                 "PT")
    # myFluid.print_state()

    hex_act = cb.models.components.heat_exchanger_thermo_v2.StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
                                state_sec_out[2],
                                d_temp_separation_min=D_TEMP_MIN)
    

    factor0 = hex_act.find_pinch()
    if hex_act.warning == 0:
        return hex_act.dt_mean
    return 80*hex_act.dt_mean

bound_act =Bounds(lb =[p_start*.75], ub =[p_start *1.1])
tolerance = 5e-1
t0 = time()
res_scalar = minimize_scalar(to_opt,
                             bounds =[.75*p_start, 1.1*p_start],
                             #tol=tolerance,
                             options ={"maxiter": 14,
                                       "disp": True,
                                       "xatol":tolerance}
                             )
print(res_scalar)
t1 =time()
result = minimize(to_opt,p_start,
                  method='Nelder-Mead',
                  tol=tolerance,
                  bounds=bound_act,
                  options ={"maxiter": 14,
                            "disp": True})
print(result)
t2 =time()
result = minimize(to_opt,p_start,
                  method='L-BFGS-B',
                  tol=tolerance,
                  bounds=bound_act,
                  options ={"maxiter": 14,
                            "disp": True})
t3 =time()
print(result)
print(t1-t0, t2-t1, t3-t2)
