# -*- coding: utf-8 -*-
"""
Local optimization of a heat pump.

pressure levels and working fluid mixture composition is varied.

Part of carbatpy

Created on Tue Jul 23 13:21:18 2024

@author: atakan
"""

import copy
import json
from time import time
# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import minimize, minimize_scalar, Bounds  # root, root_scalar
import matplotlib.pyplot as plt
import carbatpy as cb


def p_var_for_opt_hp(pressures_x,
                     fixed_p=None,
                     verbose=False,
                     **kwargs):
    """Calculates -cop for given pressure levels and mole fractions -- for minimization.

    For set_fl_state the value fixed_p['p_select']["setting"] is important. If it is
    'auto' nothing is changed e.g. {"optimize": "no", "setting": "auto", 
     "p_low": pressures_x[0],"p_high": pressures_x[1]} and an evaluation is calculated for
    the given parameters. Anything else uses the values in pressures_x!


    Parameters
    ----------
    pressures_x : np.array
        the values to be varied here p_low, p_high and all but the last mole fraction.
    fixed_p : dictionary, optional
        all other parameters needed for the heat pump calculatiob (see there). The default is None.
    verbose : TYPE, optional
        DESCRIPTION. The default is False.
    **kwargs : TYPE
        if evalute = True, nit the cop is returned, but the heat pump instance.
        Better do NOT use this option!

    Returns
    -------
    TYPE
        -cop or HeatPump instance at the desired (optimal) point.

    """

    evaluate = kwargs.get("evaluate", None)
    fixed = copy.copy(fixed_p)
    n_sp = len(pressures_x) - 2
    mole_fract = np.zeros(n_sp)
    mole_fract[:-1] = pressures_x[3:]
    if not 0 < mole_fract[:-1].sum() < 1:
        return 160 * abs( mole_fract[:-1].sum())
    x_last = 1 - mole_fract.sum()
    mole_fract[-1] = x_last
    fixed["fluids_all"]["WORKING"][1] = mole_fract

    
    if evaluate:
        p_select = {"optimize": "no",  # is unused!
                    "setting": "auto",  # this value is important in set_fl_state
                    "p_low": pressures_x[0],
                    "p_high": pressures_x[1],
                    }
    else:

        p_select = {"optimize": "p, dT_superheat and x",  # is unused!
                    "setting": "fixed-p",
                    "p_low": pressures_x[0],
                    "p_high": pressures_x[1],
                    }
    fixed["D_T_SUPER"] = pressures_x[2]
    fixed["P_WORKING"] = p_select
    
    

    hp_act = cb.hp_simple.HeatPump(fixed)
    cop = hp_act.calc_heat_pump(verbose=False)
    if verbose:
        formatted_list = [f"{num:.2f}" for num in [*pressures_x]]
        print("\nIn opt:", ", ".join(formatted_list))
        print(hp_act.warning,
              cop,
              p_select,
              fixed["P_WORKING"],
              fixed["D_T_SUPER"],
              fixed["fluids_all"]["WORKING"])
    if evaluate is not None:
        hp_act.hp_plot()
        hp_act.save_to_file()
        return hp_act
    if len(hp_act.warning) == 0:  # for minimization
        return -cop
    return 100 * cop


def my_save(a, fn=None):
    if fn is None:
        fn = cb.CB_DEFAULTS["General"]["RES_DIR"]+"\\opti-test.yml"
    a = cb.hp_simple.HpVal(a)
    a.save_to_file(fn)

def set_res_to_fixed(hp_act, values, names):
    """
    Change the fxed points to the optimal values
    
    Only for optimization of the two working fluid pressures (must be first),
    another value (actually dT_Superheat) and the mole fractions.

    Parameters
    ----------
    hp_act : HeatPump
        the actual heat pump instance.
    values : list/array
        the five values to be set.
    names : list of strings
        the names of the values to be set, as given in the fixed_points
        dictionary.

    Returns
    -------
    dictionary
        with fixed points.

    """
    n_species =len(values)-2
    mole_fract =np.zeros(n_species)
    mole_fract[:-1] = values[3:]
    mole_fract[-1] = 1 - mole_fract.sum()
    hp_act.fixed_points["fluids_all"]["WORKING"][1] = mole_fract
    
    for ii, v_act in enumerate(values[:-n_species+1]):
        if ii <2:
            hp_act.fixed_points['P_WORKING'][names[ii]]=v_act
        else:
            hp_act.fixed_points[names[ii]]=v_act
    return copy.copy(hp_act.fixed_points)
    

if __name__ == "__main__":
    # -----------------------------------------------------------------------------------
    # Set the starting point from the standard heat pump file and calculate pressures etc.
    
    fn0= cb.CB_DEFAULTS['General']['CB_DATA']+'\\'
    fn0=fn0+'hp-input-dict_opt_px20250124.json'
    with open(fn0,"r") as file:
              dict_ini = json.load(file)
    inputs = cb.hp_simple.HpVal.load_from_file(fn0)
    fixed_points = inputs.to_dict()
    act_points = copy.copy(fixed_points)
    hpn = cb.hp_simple.HeatPump(fixed_points)
    print(fixed_points, hpn.evaluation)
    
    cop_n = hpn.calc_heat_pump(verbose=False)
    print(f"Initial cop: {cop_n:.3f}")
    
    ps = ["p_low", "p_high"]
    sh = ["D_T_SUPER"]
    # this should be used when pressures are set and not calculated
    p_w = [hpn.fixed_points["P_WORKING"][key] for key in ps]
    dt_sh = [hpn.fixed_points[key] for key in sh]
    # here we use the previously calculated values
    p_w = [hpn.fixed_points[key] for key in ps]
    fl_all = hpn.fixed_points["fluids_all"]

    pressures_act = [*p_w,*dt_sh,*fl_all["WORKING"][1][:-1]]

    
   # set boundaries and tolerance
    b_min = [1.0e5, 3.0e5 ,15, 0.1]
    b_max = [3.0e5, 21.0e5 ,15, 0.1]
    bound_act = Bounds(lb=b_min,
                       ub=b_max)
    tolerance = 5e-4  # should be good enough
    max_iter = 2000
    t0 = time()
    
    opt_names =["p_low", "p_high", "D_T_SUPER"]

    result = minimize(p_var_for_opt_hp,
                      pressures_act,
                      args=(
                            fixed_points,
                            {"verbose": False}),
                      method='Nelder-Mead',
                      tol=tolerance,
                      bounds=bound_act,
                      options={"maxiter": max_iter, # can take long!
                               "disp": True})
    t1 = time()
    directory = cb.CB_DEFAULTS["General"]["RES_DIR"]
    filename = directory+"\\hp_opti"
    print(result, "\ntime:", t1-t0)
    
    # The next lines are new. Here the optimal point is re-evaluated and plotted
    act_points = set_res_to_fixed(hpn, result.x, opt_names)
    hp_opt = cb.hp_simple.HeatPump(act_points)
    cop = hp_opt.calc_heat_pump(verbose=False)
    hp_opt.hp_plot()
    
    
    hp_opt.opti_result=result
    
    hp_opt.save_to_file(filename+"3b.json")
    hp_opt.save_to_file(filename+"3b.yaml")
    
    
    
    
    hp_opt_d = hp_opt.to_dict()
    print(hp_opt_d)
    print(fixed_points==act_points)
    dict_final ={}
    for key in dict_ini:
        dict_final[key]=hp_opt_d["fixed_points"][key]
    final = cb.hp_simple.HpVal(dict_final)
    final.save_to_file(filename+"opti-input.yaml")
    print("Warning=", hp_opt.warning)
    print("COP=" ,hp_opt.evaluation['COP'])
    print("dT min Condenser=" ,hp_opt.evaluation['condenser']['dT-mean'])
    print("dT min evaporator=" ,hp_opt.evaluation['evaporator']['dT-mean'])
    print("P min=" ,hp_opt.evaluation['p_low'])
    print("P max=" ,hp_opt.evaluation['p_high'])
    print("xCO2=",hp_opt.fluids_all['WORKING'][1][0])
    print("x Butane=",hp_opt.fluids_all['WORKING'][1][1])
    print(f"exergy destruction per device: {hp_opt.evaluation['exergy_destruct_device']}")
    print(result.x)
    
