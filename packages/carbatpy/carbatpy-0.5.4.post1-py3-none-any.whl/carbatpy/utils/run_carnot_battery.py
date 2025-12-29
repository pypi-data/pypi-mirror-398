# -*- coding: utf-8 -*-
"""
Created on Tue May 21 13:56:39 2024

@author: atakan
"""


import copy
import numpy as np
import matplotlib.pyplot as plt

import carbatpy as cb

_RESULTS_ = cb._RESULTS_DIR

cb._T_SURROUNDING =288.15
if __name__ == "__main__":
    # -------HEAT PUMP------------------------------

    FLUID = 'Propane * Butane * Pentane * Hexane'
    # comp = [.15, 0.55, 0.0, 0.30]
    # comp = [0.4,	0.3,	0.3, 0.0]  # [0.164,.3330,.50300,0.0]
    # comp = [.05, 0.65, 0.0, 0.30]
    comp = [0.771733787, 0.0222759488, 0.178685867, 0.027304397199999997] 
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
    _ETA_S_ = 0.6  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    T_MAX = 363.15 # 369.
    T_MIN = 250.15
    _STORAGE_T_IN_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_IN_ = _STORAGE_T_IN_
    _STORAGE_T_OUT_ = T_MAX  # 395.0
    _COLD_STORAGE_T_OUT_ = T_MIN
    _STORAGE_P_IN_ = 5e5  # pressure
    _COLD_STORAGE_P_IN_ = 5e5
    _Q_DOT_MIN_ = 1e3  # heat_flow rate to storage (W)
    _D_T_SUPER_ = 3.8  # super heating of working fluid
    _D_T_MIN_ = 2.  # minimum approach temperature (pinch point)
    _D_T_EVAP = 5.0
    _D_T_COND = -7
    # high T-storages
    state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

    #  low T storages:
    state_cold_out = coldFluid.set_state(
        [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid
    T_DEW = _STORAGE_T_OUT_  +_D_T_COND# + _D_T_MIN_
    state_in_cond = myFluid.set_state([T_DEW, 1.], "TQ")  # find high pressure
    state_out_cond = myFluid.set_state([_STORAGE_T_IN_ + _D_T_MIN_,
                                        state_in_cond[1]], "TP")
    state_satv_evap = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_-_D_T_EVAP, 1.], "TQ")  # find minimum pressure
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
    
    ###########################################################################
    DEFAULT_DIR =  cb.CB_DEFAULTS["General"]["CB_DIR"]+"\\data\\"
    DEFAULT_FILE = DEFAULT_DIR+"hp-input-dictvariables"
    inputs = cb.hp_simple.HpVal.load_from_file(DEFAULT_FILE+".json")
    # print(DEFAULT_FILE)

    INPUTS = inputs.to_dict()
    
    hp0 = cb.hp_simple.HeatPump(INPUTS)
    print(hp0.evaluation)
    cop = hp0.calc_heat_pump(verbose=True)
    print(hp0.evaluation)
    fig_ax_act = hp0.hp_plot()
    print(hp0.evaluation, "\n----------------\n")

    out = hp0.evaluation
    print(f"Min and mean dT evaporator: {out['evaporator']['dT-min']}, {out['evaporator']['dT-mean']}")
    print(f"Min and mean dT condenser: {out['condenser']['dT-min']}, {out['condenser']['dT-mean']}")

    print(
        f"COP: {cop},p-ratio: {out['p_high']/out['p_low']:.2f}, p_low {out['p_low']/1e5:.2f} bar")

    print(
        f'exergy loss rate: {out["exergy_loss_rate"]}, eff: {1-out["exergy_loss_rate"]/out["Power"]:.4f}')

    #
    my_dict = cb.hp_simple.read_hp_results(_RESULTS_ +
                                           "\\last_T_H_dot_plot_hp_evaluation_dict.npy")
    T_MAX = hp0.all_states[1][-1][0]  # actual highest storage temperature
    T_MIN = hp0.all_states[3][-1][0]  # actual minimum storage temperature

    # ----------------------ORC ----------------

    # FLUID = "Propane * Butane * Pentane * Hexane"
    # comp = [.75, 0.05, 0.15, 0.05]
    # comp = [0.4,	0.3,	0.3, 0.0]  # [0.164,.3330,.50300,0.0]

    # FLS = "Water"  # Storage fluid
    # FLCOLD = "Methanol"  # Storage fluid for low T
    FLENV = "Water"  #

    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])

    coldFlm = cb.fprop.FluidModel(FLCOLD)
    coldFluid = cb.fprop.Fluid(coldFlm, [1.])

    envFlm = cb.fprop.FluidModel(FLENV)
    envFluid = cb.fprop.Fluid(secFlm, [1.])

    # Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
    # pressures (p in Pa)
    _ETA_S_ = 0.7  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    _ETA_S_P_ = 0.6  # pump
    _STORAGE_T_OUT_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_OUT_ = cb._T_SURROUNDING
    _ENV_T_IN_ = cb._T_SURROUNDING
    _ENV_T_OUT_ = cb._T_SURROUNDING + 5.
    _STORAGE_T_IN_ = T_MAX  # 395.0
    _COLD_STORAGE_T_IN_ = T_MIN
    _STORAGE_P_IN_ = 5e5
    _COLD_STORAGE_P_IN_ = 5e5
    _ENV_P_IN_ = 5e5
    _Q_DOT_MIN_FACTOR = 1.  # and heat_flow rate (W)
    _D_T_SUPER_ = 5  # super heating of working fluid
    _D_T_MIN_ = 2.  # minimum approach temperature (pinch point)
    _COP_CHARGING = cop  # needed to calculate Q_env_discharging
    _T_REDUCTION_EVAP = -25  # if the curves cross in the evaporator this parameter may help
    _T_INCREASE_COND = 17.5
    # environment for heat transfer
    state_env_out = envFluid.set_state([_ENV_T_OUT_, _ENV_P_IN_], "TP")
    state_env_in = envFluid.set_state([_ENV_T_IN_, _ENV_P_IN_], "TP")

    # high T-storages
    state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

    #  low T sorages:
    state_cold_out = coldFluid.set_state(
        [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid

    state_satv_evap = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_+_T_REDUCTION_EVAP, 1.], "TQ")  # find high pressure
    p_high = state_satv_evap[1]

    T_OUT = _STORAGE_T_IN_ - _D_T_MIN_
    # Evaporator input comes from the pump-output

    state_out_evap = myFluid.set_state([p_high,
                                        T_OUT], "PT")
    # low pressure, condenser # BA 2023-11-14 three points needed: low, environment and slightly higher
    T_SATL = _COLD_STORAGE_T_IN_ + _D_T_MIN_ + \
        _T_INCREASE_COND  # BA 2024-05-21 be careful
    state_out_cond = myFluid.set_state([T_SATL, 0.], "TQ")  # find low pressure
    p_low = state_out_cond[1]
    # BA changed 2023-12-13 the fixed starting point for the cycle is the  fluid
    # state before the pump now.

    # the other states in the condenser are fixed by the expander outlet and
    # the Q_total : Q_low_stored ratio    eventually p_low must be varied until
    # the balance is fulfilled, since m_dot_w is fixed by the evaporator!

    FIXED_POINTS_ORC = {"eta_s": _ETA_S_,  # expander
                        "eta_s_p": _ETA_S_P_,  # pump
                        "p_low": p_low,
                        "p_high": p_high,
                        "T_hh": _STORAGE_T_IN_,
                        "h_h_out_sec": state_sec_out[2],
                        "h_h_out_w": state_out_evap[2],
                        "h_l_out_cold": state_cold_out[2],
                        "h_l_out_w": state_out_cond[2],
                        "h_env_in": state_env_in[2],
                        "h_env_out": state_env_out[2],
                        "T_hl": _STORAGE_T_OUT_,
                        "T_lh": _COLD_STORAGE_T_OUT_,
                        "T_ll": _COLD_STORAGE_T_IN_,  # 256.0,
                        "Q_dot_h": _Q_DOT_MIN_ * _Q_DOT_MIN_FACTOR,
                        "d_temp_min": _D_T_MIN_,
                        "cop_charging": cop  # needed to calculate Q_env_discharging
                        }

    orc0 = cb.orc_simple.OrganicRankineCycle(
        [myFluid, secFluid, envFluid, coldFluid], FIXED_POINTS_ORC)
    eta_dis = orc0.calc_orc()
    print(f"eta(ORC): {eta_dis:.3f}, COP(HP): {cop:.3f}")
    orc0.hp_plot(fig_ax=fig_ax_act)
    print(f"RTE: {cop*eta_dis:.3f}")
    print(f"warnings: HP {hp0.warning}; ORC {orc0.warning}")
