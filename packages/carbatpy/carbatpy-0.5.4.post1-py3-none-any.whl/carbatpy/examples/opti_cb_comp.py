# -*- coding: utf-8 -*-
"""
Example for Optimization of a Carnot battery, with a heat pump (heat_pump_comp) 
for charging and an ORC for discharging using scipy.optimize

Composition and high pressure (condenser) of the working fluid, and the low
temperature of the double tank cold storage are optimization variables for the heat pump. All
other parameters are fixed in a yaml file (io-cycle-data.yaml). For the ORC, the same
composition is used and only the two working fluid pressure levels are optimized.

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

OPTI = True
HOW_OPT = "bas_hop"  #'shgo' # "dif_evol"  # "local" #
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-")
STORE_FILENAME = cb.CB_DEFAULTS["General"]["RES_DIR"] +"\\"+ current_date + "cb_opt_result"
POWER_C = 2000. # compressr power of heat pump
DIR = cb.CB_DEFAULTS["General"]["CB_DATA"]


# Ordner erstellen und YAML schreiben
dir_res = Path(STORE_FILENAME)
dir_res.mkdir(exist_ok=True)

datei = dir_res / 'config_bound.yaml'
res_dat = dir_res / 'opt_res.yaml'
file_res = dir_res / (current_date + "cb_opti_res.csv")


dir_names_both = {"hp": DIR+"\\io-cycle-data.yaml",
                  "orc": DIR+"\\io-orc-data.yaml"}
for io_file in dir_names_both.values():
    shutil.copy2(io_file, dir_res)
    

# optimization variables, must be present in the file above
conf_hp = {"cold_storage": {"temp_low": 265.},
          "working_fluid": {"p_high": 1.45e6,
                            "p_low": 1.8e5,
                            'fractions': [.438, .4310, 0.131,  0.0000],
                            }
          }
conf_orc = {"working_fluid": {"p_high": 4.71e5,
                            "p_low": 2.21e5,
                            }
            }

# bounds of the optimization variables
bounds_hp = {"cold_storage": {"temp_low": [265, 277]},
            "working_fluid":
            {"p_high": [8.e5, 01.9e6],
             "p_low":[1e5, 2.9e5],
             'fractions': [[0.3, .85], [0.0, .7], [0.0, 0.3], [0, 0.25]]},
            }
bounds_orc = {"working_fluid":
            {"p_high": [4e5, 0.82e6],
             "p_low":[2.10e5, 3.9e5],},
            }

configs_m ={"hp" : conf_hp,
          "orc": conf_orc}
bounds_m = {"hp" : bounds_hp,
            "orc" : bounds_orc}

with datei.open('w') as f:
    yaml.dump({"configs":configs_m,
               "bounds":bounds_m,
               'power_compressor': POWER_C}, f, default_flow_style=False,
               sort_keys=False)

# WICHTIG: Der ausführbare Code muss in diesem Block stehen!
if __name__ == "__main__":
    if OPTI:
        # for optimization:
        print("Carnot battery optimization is running. It may take a while!")
        opt_res, paths = cb.opti_cycle_comp_helpers.optimize_cb(
            dir_names_both, POWER_C, configs_m, bounds_m,
            optimize_global=HOW_OPT,
            workers=1,
            maxiter=1,
            #opt_opt = -.03,
            )
        print(opt_res)
        with open(dir_res / "paths.pkl", "wb") as pf:
            pickle.dump(paths, pf)
        co_n = cb.opti_cycle_comp_helpers.extract_cb_conf_from_x(opt_res.x, 
                                                                 configs_m, 
                                                                 paths)
        rte, res_ = cb.cb_comp.cb_calc(dir_names_both, POWER_C, config=co_n, plotting=True)
        col_names = cb.opti_cycle_comp_helpers.extract_column_names_from_config(res_["hp"]['output']["config"], paths) + ["rte"]
        for key in res_.keys(): # save plots
            file_fig = dir_res / (current_date + key+"_cb_opti_res.png")
            res_[key]["figure"].savefig(file_fig)
        if HOW_OPT== 'dif_evol':
            res_combi = np.column_stack([opt_res.population, opt_res.population_energies])
            df = pd.DataFrame(res_combi, columns=col_names)
            df.to_csv(file_res, sep=",", index=False)
        else:
            res_dict ={'x': (opt_res.x).tolist(),
                       'fun':float(opt_res.fun),
                       'success':opt_res.success,
                       'message':opt_res.message,
                       'results':dict(zip(col_names, (opt_res.x).tolist()))}
            with res_dat.open('w') as f:
                yaml.dump(res_dict, f, default_flow_style=False,
                           sort_keys=False)
            
        
        