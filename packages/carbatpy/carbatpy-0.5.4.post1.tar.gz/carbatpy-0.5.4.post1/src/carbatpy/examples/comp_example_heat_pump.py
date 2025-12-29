# -*- coding: utf-8 -*-
"""
An example of using the classes in comp to calculate a heat pump.

Created on Mon Aug 12 17:28:32 2024

@author: atakan
"""

import matplotlib.pyplot as plt
import carbatpy as cb


if __name__ == "__main__":
    # in the following yaml file most parameters are set
    dir_name_out = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"
    
    #if you want to replace some of the values of the yaml file you can wrinte
    # them in a dictionary:
    conf_m = {"cold_storage": {"temp_low": 274.},
              "working_fluid": {"p_high": 1.49e6,
                                'fractions': [.4, 0.4, .20, 0.0000]},
              "process":{"fixed": {"compressor": {"power": 1000000.0}}}
              }
    
    # pass them for the calculation of the results
    res_act = cb.hp_comp.heat_pump(
        dir_name_out, config=conf_m, verbose=True, plotting =True)
    if any(ns.value != 0 for ns in res_act['warnings'].values()):
        print(f"Check Warnings, at least one deviates from 0!\n {res_act['warnings']}")
    # many results are now stored in the dictionary res_act, e.g.:
    print(f"\nThe COP is: {res_act['COP']:.2f}")


