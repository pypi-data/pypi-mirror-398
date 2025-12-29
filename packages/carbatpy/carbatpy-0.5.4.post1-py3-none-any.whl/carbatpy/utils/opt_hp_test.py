# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 13:21:18 2024

@author: atakan
"""

import copy
from time import time
# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import minimize, minimize_scalar, Bounds  # root, root_scalar
import matplotlib.pyplot as plt
import carbatpy as cb



def p_var_for_opt_hp(pressures,
                     fluids=None,
                     fixed=None,
                     t_val=None):
    
        state_out_cond = myFluid.set_state([t_val[0],
                                            pressures[1]], "TP")
        state_out_evap = myFluid.set_state([pressures[0],
                                            t_val[1]], "PT")
        fixed_new = {"eta_s": _ETA_S_,
                        "p_low": pressures[0],
                        "p_high": pressures[1],
                        "T_hh": t_val[2],
                        
                        "h_h_out_w": state_out_cond[2],
                        
                        "h_l_out_w": state_out_evap[2],
                        }
        fixed.update(fixed_new)
        # fixed["p_low"]= pressures[0]
        # fixed["p_high"]= pressures[1]
        hp_act = cb.hp_simple.HeatPump(fluids, fixed)
        print( "in opt:", pressures, t_val)  # hp_act.evaluation,
        cop = hp_act.calc_heat_pump(verbose=False)
        print(hp_act.warning, cop)
        if len (hp_act.warning) == 0: # for minimization
            return -cop
        return 10
    


if __name__ == "__main__":

    FLUID = "Propane * Butane * Pentane * Hexane"
    comp = [.75, 0.05, 0.15, 0.05]
    # comp = [0.4,	0.3,	0.3, 0.0]  # [0.164,.3330,.50300,0.0]

    FLS = "Water"  #
    FLCOLD = "Methanol"  # "Water"  #

    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])

    coldFlm = cb.fprop.FluidModel(FLCOLD)
    coldFluid = cb.fprop.Fluid(coldFlm, [1.])

    # Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
    # pressures (p in Pa)
    _ETA_S_ = 0.7  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    _STORAGE_T_IN_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_IN_ = _STORAGE_T_IN_
    _STORAGE_T_OUT_ = 363.  # 395.0
    _COLD_STORAGE_T_OUT_ = 250.15
    _STORAGE_P_IN_ = 5e5
    _COLD_STORAGE_P_IN_ = 5e5
    _Q_DOT_MIN_ = 1e3  # and heat_flow rate (W)
    _D_T_SUPER_ = 5  # super heating of working fluid
    _D_T_MIN_ = 4.  # minimum approach temperature (pinch point)
    # high T-storages
    state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

    #  low T storages:
    state_cold_out = coldFluid.set_state(
        [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid
    T_DEW = _STORAGE_T_OUT_  # + _D_T_MIN_
    state_in_cond = myFluid.set_state([T_DEW, 1.], "TQ")  # find high pressure
    state_out_cond = myFluid.set_state([_STORAGE_T_IN_ + _D_T_MIN_,
                                        state_in_cond[1]], "TP")
    state_satv_evap = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_, 1.], "TQ")  # find minimum pressure
    p_low = state_satv_evap[1]

    T_IN = _STORAGE_T_IN_ - _D_T_MIN_

    state_out_evap = myFluid.set_state([p_low,
                                        T_IN], "PT")

    FIXED_POINTS = {"eta_s": _ETA_S_,
                    "p_low": state_out_evap[1],
                    "p_high": state_in_cond[1],
                    "T_hh": _STORAGE_T_OUT_,
                    "h_h_out_sec": state_sec_out[2],
                    "h_h_out_w": state_out_cond[2],
                    "h_l_out_cold": state_cold_out[2],
                    "h_l_out_w": state_out_evap[2],
                    "T_hl": _STORAGE_T_IN_,
                    "T_lh": _STORAGE_T_IN_,
                    "T_ll": _COLD_STORAGE_T_OUT_,  # 256.0,
                    "Q_dot_h": _Q_DOT_MIN_,
                    "d_temp_min": _D_T_MIN_}

    print(
        f"p-ratio: {state_in_cond[1]/state_out_evap[1]: .2f}, p_low: {state_out_evap[1]/1e5: .2} bar")
    hp0 = cb.hp_simple.HeatPump([myFluid, secFluid, coldFluid], FIXED_POINTS)
    print(hp0.evaluation)
    cop = hp0.calc_heat_pump(verbose=True)
    print(hp0.evaluation)
    hp0.hp_plot()
    print(hp0.evaluation, "\n----------------\n")

    out = hp0.evaluation
    
    
    #----------
    # Test evaluation of a function to optimitze the two pressures of a heat pump:
    
    p_high = state_in_cond[1]
    pressures_act=[p_low, p_high]
    min_v = 0.95
    max_v =1.05 # bounds for optimization
    fluids=myFluid, secFluid, coldFluid
    fixed_act = FIXED_POINTS
    t_val=[_STORAGE_T_IN_ + _D_T_MIN_,
                T_IN,
                _STORAGE_T_OUT_]
    
    
    out_f= p_var_for_opt_hp(pressures_act,
                         fluids=fluids,
                         fixed = FIXED_POINTS,
                         t_val=t_val)
    print(f"opt-Function call. COP: {out_f}")
    
    bound_act = Bounds(lb =[p_low*min_v, p_high* min_v],
                       ub =[p_low*max_v, p_high* max_v])
    tolerance = 5e-3
    t0 = time()
    
    result = minimize(p_var_for_opt_hp,
                      pressures_act,
                      args=(fluids,
                            FIXED_POINTS,
                            t_val),
                      method='Nelder-Mead',
                      tol=tolerance,
                      bounds=bound_act,
                      options ={"maxiter": 24,
                                "disp": True})
    t1 =time()
    print(result, "time:",t1-t0)
    p_var_for_opt_hp(result.x,
                     fluids=fluids,
                     fixed = FIXED_POINTS,
                     t_val=t_val )
    
    
    #--------------------------
    
    
    print(f"Min and mean dT evaporator: {out['evaporator']['dT-min']}, {out['evaporator']['dT-mean']}")
    print(f"Min and mean dT condenser: {out['condenser']['dT-min']}, {out['condenser']['dT-mean']}")
    print(
        f"COP: {cop},p-ratio: {out['p_high']/out['p_low']:.2f}, p_low {out['p_low']/1e5:.2f} bar")

    print(
        f'exergy loss rate: {out["exergy_loss_rate"]}, eff: {1-out["exergy_loss_rate"]/out["Power"]:.4f}')

    #
    my_dict = cb.hp_simple.read_hp_results(cb._RESULTS_DIR+
                              "\\last_T_H_dot_plot_hp_evaluation_dict.npy")