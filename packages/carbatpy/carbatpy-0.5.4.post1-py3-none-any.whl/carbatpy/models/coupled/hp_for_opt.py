# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 11:13:12 2023

@author: atakan
"""

import numpy as np
import carbatpy as cb

import pandas as pd
import seaborn as sbn
import matplotlib.pyplot as plt
import datetime
dir_name = cb._RESULTS_DIR + "\\optimal_hp_fluid"
fname = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")+"threeAlkanes"
plt.style.use('seaborn-v0_8-poster')  # 'seaborn-v0_8-poster')

FLUID_COMP = "Propane * Butane * Pentane"  # " * Hexane"
comp = [.5, 0., 0.5]  # , 0.0]
# comp =[0.000,1.0,0.00,0.0]

FLS = "Water"  #
FLCOLD = "Methanol"  # "Water"  #

flm = cb.fprop.fluid_model(FLUID_COMP)
my_fluid = cb.fprop.Fluid(flm, comp)

secFlm = cb.fprop.fluid_model(FLS)
secondary_fluid = cb.fprop.Fluid(secFlm, [1.])

coldFlm = cb.fprop.fluid_model(FLCOLD)
cold_fluid_act = cb.fprop.Fluid(coldFlm, [1.])

# Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
# pressures (p in Pa)

SECONDARY_TEMP_IN = 290.0
COLD_TEMP_IN = SECONDARY_TEMP_IN
SECONDARY_TEMP_OUT = 363.  # 395.0
COLD_TEMP_OUT = 257.
SP_IN = 5E5
CP_IN = 5E5
DH_MIN = 1E3  # AND HEAT_FLOW RATE (W)
ETA_S = 0.65
D_TEMPMIN = 1.530  # MINIMUM APPROACH TEMPERATURE (PINCH POINT)
Q_DOT_H = 3000.

state_sec_in = secondary_fluid.set_state([SECONDARY_TEMP_IN, SP_IN], "TP")
state_cold_in = cold_fluid_act.set_state([COLD_TEMP_IN, CP_IN], "TP")

# working fluid
D_TEMPSUPER = 5.  # super heating of working fluid
TEMP_DEW = SECONDARY_TEMP_OUT
state_in_act = my_fluid.set_state([TEMP_DEW, 1.], "TQ")  # find minimum pressure

TEMP_IN = TEMP_DEW + D_TEMPSUPER
state_in_act = my_fluid.set_state([my_fluid.properties.pressure,
                              my_fluid.properties.temperature + D_TEMPSUPER], "PT")
p_high_act = state_in_act[1]

state_in_act = my_fluid.set_state(
    [SECONDARY_TEMP_IN - D_TEMPSUPER, 1.], "TQ")  # find minimum pressure
p_low_act = state_in_act[1]

state_in_act = my_fluid.set_state([p_low_act,
                              SECONDARY_TEMP_IN - D_TEMPMIN], "PT")
print(f"p-ratio: {p_high_act/p_low_act: .2f}, p_low: {p_low_act/1e5: .2} bar")

state_in_act = my_fluid.set_state([p_low_act, TEMP_IN], "PT")

fixed_points_act = {"eta_s": ETA_S,
                "p_low": p_low_act,
                "temp_hh": SECONDARY_TEMP_OUT,
                "temp_hl": SECONDARY_TEMP_IN,
                "temp_lh": SECONDARY_TEMP_IN,
                "temp_ll": COLD_TEMP_OUT,
                "q_dot_h": Q_DOT_H,
                "d_tempmin": D_TEMPMIN}

hp0_act = cb.hp_simple.heat_pump([my_fluid, secondary_fluid, cold_fluid_act],
                             fixed_points_act)
cop_act = hp0_act.calc_p_high(p_high_act)
hp0_act.hp_plot()
out = hp0_act.evaluation
print(
    f"COP: {out[0]/out[1]:.2f},p-ratio: { out[2]/out[3]:.2f}, p_low {out[3]/1e5:.2f} bar")


def hp_comp_cop(composition, work_fluid, sec_fluid, cold_fluid,
                fixed_points, d_tempsuper=5.0, opt=+1):
    # working fluid
    sum3 = np.sum(composition)
    if sum3 > 1:
        return 0

    last = 1-sum3
    new_composition = np.array([*composition, last])

    work_fluid.set_composition(new_composition)
    temp_dew = fixed_points["temp_hh"]
    state_in = work_fluid.set_state(
        [temp_dew, 1.], "TQ")  # find minimum pressure

    # TEMP_IN = temp_dew + D_TEMPSUPER
    state_in = work_fluid.set_state([work_fluid.properties.pressure,
                                    work_fluid.properties.temperature + D_TEMPSUPER], "PT")
    p_high = state_in[1]

    state_in = work_fluid.set_state(
        [fixed_points["temp_lh"] - d_tempsuper, 1.], "TQ")  # find minimum pressure
    p_low = state_in[1]

    state_in = my_fluid.set_state([p_low,
                                  SECONDARY_TEMP_IN - D_TEMPMIN], "PT")
    fixed_points["p_low"] = p_low
    hp0 = cb.hp_simple.heat_pump(
        [work_fluid, sec_fluid, cold_fluid], fixed_points)
    cop = hp0.calc_p_high(p_high)
    print("Result-hp-opt:", new_composition, np.sum(new_composition),
          cop, p_low, p_high, p_high/p_low)
    if opt == -1:
        return cop * opt

    return cop, p_low/1e5, p_high/1e5


all_res = []
x0_range = np.linspace(0.0, 0.6, 12)
x1_range = np.linspace(0, 0.6, 10)
for x0 in x0_range:
    for x1 in x1_range:
        if x0+x1 <= 1:
            x2 = 1-(x0+x1)
            comp = np.array([x0, x1])
            results = hp_comp_cop(comp, my_fluid, secondary_fluid,
                                  cold_fluid_act,
                                  fixed_points_act,
                                  d_tempsuper=D_TEMPSUPER,
                                  opt=+1)
            if results[0] > 1:
                new = np.array([*results, x0, x1, x2,
                                *fixed_points_act.values()])
                all_res.append(new)

names = ["COP", "$p_{low}$", "$p_{high}$", "$x_{Propane}$",
         "$x_{Butane}$", "$x_{Pentane}$", *fixed_points_act.keys()]
all_res = np.array(all_res)
dframe = pd.DataFrame(all_res, columns=names)
dframe.to_csv(dir_name+"\\"+fname+".csv")
dframe2 = dframe.round(3)
f, ax = plt.subplots(figsize=(10, 6), layout="constrained")
fff = sbn.scatterplot(x=names[4], y=names[5],
                      hue=names[2], size=names[0], data=dframe2, ax=ax)
sbn.move_legend(fff, "upper left", bbox_to_anchor=(1, 1))
f.savefig(dir_name+"\\"+fname+".png")
# bounds = ((0.05, 0.95), (0.00, 0.65))


# def constr(comp):
#     print(comp, np.sum(comp))
#     return 1-np.sum(comp)

# res = opt.differential_evolution(hp_comp_cop, bounds,
#                args=(my_fluid, secFluid, cold_fluid_act, fixed_points)
#                )
# print(res)
