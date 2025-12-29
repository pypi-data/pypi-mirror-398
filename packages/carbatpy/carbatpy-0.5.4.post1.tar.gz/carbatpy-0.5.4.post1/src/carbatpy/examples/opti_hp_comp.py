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
import datetime
from pathlib import Path
import shutil
import yaml
import pickle

# Konfiguration und Konstanten (diese können außerhalb des main-Blocks stehen)
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-")
OPTI = True
HOW_OPT = "dif_evol"  # "local" #
STORE_FILENAME = cb.CB_DEFAULTS["General"]["RES_DIR"] +"\\" + \
    current_date + "hp_opt_results"

DIR = cb.CB_DEFAULTS["General"]["CB_DATA"]

file_config = DIR + '\\io-cycle-data.yaml'

# Ordner erstellen und YAML schreiben
dir_res = Path(STORE_FILENAME)
dir_res.mkdir(exist_ok=True)

datei = dir_res / 'config_bound.yaml'
res_dat = dir_res / 'opt_res.yaml'
file_res = dir_res / (current_date + "hp_opti_res.csv")
# optimization variables, must be present in the file above
conf_m = {"cold_storage": {"temp_low": 270.},
          "compressor": {'dt_superheat': 5},
          "working_fluid": {"p_high": 1.65e6,
                            "p_low": 1.67e5,
                            'fractions': [.80, 0.2]}}
# bounds of the optimization variables
bounds_m = {"cold_storage": {"temp_low": [265, 277]},
            "compressor": {'dt_superheat': [3, 20]},
            "working_fluid":
            {"p_high": [5e5, 02.1e6],
             "p_low": [1e5, 4e5],
             'fractions': [[0.7, 1.], [0.0, 0.4]]},

            }

# Run heat pump without optimization, with the configuration conf_m:
if __name__ == "__main__":
    res_m = cb.hp_comp.heat_pump(
        file_config, config=conf_m,
        verbose=True, plotting=True)
    if any(ns.value != 0 for ns in res_m["warnings"].values()):
        print(
            f"Check Warnings, at least one deviates from 0!\n {res_m['warnings']}")

    if OPTI:
        # for optimization:

        opt_res, paths = cb.opti_cycle_comp_helpers.optimize_wf_heat_pump(
            file_config,
            conf_m,
            bounds_m,
            optimize_global=HOW_OPT,
            workers=1,
            maxiter=50,
            verbose=True,)
        print(opt_res)

        with open(dir_res / "paths.pkl", "wb") as pf:
            pickle.dump(paths, pf)
        co_n = cb.opti_cycle_comp_helpers.insert_optim_data(conf_m,
                                                            opt_res.x,
                                                            paths)
        res_ = cb.hp_comp.heat_pump(
            file_config, config=co_n, plotting=True)
        col_names = cb.opti_cycle_comp_helpers.extract_cycle_column_names_from_config(
            res_['output']["config"], paths) + ["COP"]
        file_fig = dir_res / (current_date + "_hp_opti_res.png")
        res_["figure"].savefig(file_fig)
        if HOW_OPT == 'dif_evol':
            res_combi = np.column_stack(
                [opt_res.population, opt_res.population_energies])
            df = pd.DataFrame(res_combi, columns=col_names)
            df.to_csv(file_res, sep=",", index=False)
        
        res_dict = {'x': (opt_res.x).tolist(),
                    'fun': float(opt_res.fun),
                    'success': opt_res.success,
                    'message': opt_res.message,
                    'results': dict(zip(col_names, (opt_res.x).tolist()))}
        with res_dat.open('w') as f:
            yaml.dump(res_dict, f, default_flow_style=False,
                      sort_keys=False)
