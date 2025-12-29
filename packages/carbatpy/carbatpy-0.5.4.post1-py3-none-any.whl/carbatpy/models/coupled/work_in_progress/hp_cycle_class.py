# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 11:19:24 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""

import carbatpy as cb

dir_name = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"
conf_m = {"cold_storage": {"temp_low": 274.},
          "working_fluid": {"p_high": 1.49e6,
                            'fractions': [.4, 0.4, .20, 0.0000]}}

hp_act = cb.comp.main(dir_name, new_config=conf_m)