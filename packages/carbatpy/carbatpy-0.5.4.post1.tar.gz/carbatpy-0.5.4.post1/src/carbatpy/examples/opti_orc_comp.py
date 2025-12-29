# -*- coding: utf-8 -*-
"""
Example for Optimization of a heat pump (heat_pump_comp) using scipy.optimize

Composition and high pressure (condenser) of the working fluid, and the low
temperature of the double tank cold storage are optimization variables. All
other parameters are fixed in a yaml file (io-cycle-data.yaml).

Created on Mon Aug  4 13:12:24 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""


import numpy as np
import pandas as pd
import carbatpy as cb

OPTI = True
HOW_OPT = "dif_evol"
STORE_FILENAME = None
COP = 3.05
Q_DOT_HIGH = 3000.
WITH_COMPOSITION = True

dir_name_out = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-orc-data.yaml"

# optimization variables, must be present in the file above
if WITH_COMPOSITION:
    conf_m = {"cold_storage": {"temp_low": 254.},
              "working_fluid": {"p_high": .49e6,
                                'fractions': [.74, .0, 0.26,  0.0000]}}
    # bounds of the optimization variables
    bounds_m = {"cold_storage": {"temp_low": [255, 277]},
                "working_fluid":
                {"p_high": [4e5, 0.6e6],
                 'fractions': [[0.0, .85], [0.0, .005], [0, 0.5], [0, 0.5]]},
    
                }
else:
    conf_m = {"cold_storage": {"temp_low": 254.},
              "working_fluid": {"p_high": .58e6,
                                'p_low': 3.5e5}}
    # bounds of the optimization variables
    bounds_m = {"cold_storage": {"temp_low": [250, 277]},
                "working_fluid":
                {"p_high": [4.1e5, 1.1e6],
                 'p_low': [3.0e5, 3.9e5]},
    
                }

# Run heat pump without optimization, with the configuration conf_m:

res_m = cb.orc_comp.orc(
    dir_name_out, COP, Q_DOT_HIGH, config=conf_m, verbose=True, plotting=True)
if any(ns.value != 0 for ns in res_m['warnings'].values()):
    print(f"Check Warnings, at least one deviates from 0!\n {res_m['warnings']}")

if __name__ == '__main__':
    
    if OPTI:
        # for optimization:
        print('\nOptimization is running ...\n')
    
        opt_res, paths = cb.opti_cycle_comp_helpers.optimize_orc(
            dir_name_out, COP, Q_DOT_HIGH, 
            conf_m, bounds_m, 
            optimize_global=HOW_OPT,
            verbose=True,
            maxiter =1)
        print(opt_res)
    
        if HOW_OPT == "dif_evol":  # or: "dif_evol", "bas_hop"
    
    
            df = pd.DataFrame(opt_res.population)
            df["eta-weighted"] = opt_res.population_energies
    
            p_l = []
            c6 = []
            p_ratio = []
            etas = []
            for o_val in opt_res.population:
                try:
                    conf_o = cb.opti_cycle_comp_helpers.insert_optim_data(
                        conf_m, o_val, paths)
                    # conf_o = {"working_fluid": {"p_high": o_val[0],  'fractions':  [
                    #     *o_val[1:], 1 - np.sum(o_val[1:])]}}
                    res_o = cb.orc_comp.orc(
                        dir_name_out, COP, 
                        Q_DOT_HIGH, 
                        config=conf_o, 
                        verbose=True, 
                        plotting=True)
                    p_l_opt = res_o['output']['start']['p_low']
                    p_h_opt = conf_o["working_fluid"]["p_high"]
                    p_l.append(p_l_opt)
                    c6.append(1-np.sum(o_val[1:]))
                    p_ratio.append(p_h_opt / p_l_opt)
                    etas.append(res_o["eta_th"])
                except Exception as e:
                    print("Error in ORC-Opti:", type(e), e)
                    p_ratio.append(-10)
                    etas.append(-10)
            #df["hexane"] = c6  # name for this input file
            #df["p_low"] = p_l
            df["p_ratio"] = p_ratio
            df['eta_th'] = res_o["eta_th"]
            if STORE_FILENAME is not None:
                df.to_csv(
                    STORE_FILENAME,  # should be '.csv'
                    index=False)
        else:
            o_val = opt_res.x
            conf_o = cb.opti_cycle_comp_helpers.insert_optim_data(
                conf_m, o_val, paths)
            res_o = cb.orc_comp.orc(
                dir_name_out, COP, Q_DOT_HIGH, config=conf_o, verbose=True, plotting=True)
            print(f"eta_th-Optimized by {HOW_OPT}: {res_o['eta']:.2f}")
