# -*- coding: utf-8 -*-
"""
Calculation of a Carnot Battery (PTES) with two energy storages.


Created on Tue Aug  5 12:33:52 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""
import carbatpy as cb


def cb_calc(dir_names, **kwargs):

    new_config = kwargs.get("config", {"hp": None, "orc": None})  # for optimizations
    verbose = kwargs.get("verbose", False)
    plotting = kwargs.get("plotting", False)

    cop_h, ou_h, wa_h, fi_h, ax_h = cb.hp_comp.heat_pump(
        dir_names["hp"], config=new_config["hp"], verbose=verbose, plotting=plotting)
    
    if any(ns.value != 0 for ns in wa_h.values()):
        print(f"Check HP Warnings, at least one deviates from 0!\n {wa_h}")
        return -10
    
    print(f"COP: {cop_h:.3f}")
    q_h = -ou_h["condenser"]["q_dot"]
    # same fluid:
    orc_config = cb.utils.io_utils.read_config(dir_names["orc"])
    from_hp_config = {"working_fluid" : {"fractions": ou_h["config"]["working_fluid"]["fractions"],
                                    "species" :ou_h["config"]["working_fluid"]["species"]},
                  "cold_storage" :  {"temp_low" : ou_h["config"]["cold_storage"]["temp_low"]},
                  "hot_storage" : {"temp_high" : ou_h["config"]["hot_storage"]["temp_high"]}}
    for key in from_hp_config:
        if key in orc_config :
            orc_config[key].update(from_hp_config[key])
        else:
            orc_config[key] = from_hp_config[key]
    eta, ou_o, wa_o, fig_o, ax_o = cb.orc_comp.orc(orc_config,
                                                   cop_h,
                                                   q_h,
                                                   config=new_config["orc"],
                                                   plotting=True)
    if any(ns.value != 0 for ns in wa_o.values()):
        print(f"Check ORC Warnings, at least one deviates from 0!\n {wa_h}")
        return -20
    
    print(f"eta: {eta:.3f}")
    return eta*cop_h


if __name__ == "__main__":
    dir_names_both = {"hp": cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml",
                      "orc": cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-orc-data.yaml"}
    rte = cb_comp(dir_names_both, plotting =True)
    print(f"RTE: {rte:.3f}")