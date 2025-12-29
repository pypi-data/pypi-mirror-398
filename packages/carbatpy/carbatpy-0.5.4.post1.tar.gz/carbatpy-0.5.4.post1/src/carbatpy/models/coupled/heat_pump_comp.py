# -*- coding: utf-8 -*-
"""
Heat pump with two two-tank storage, with the new component (comp.py) formulation.

Created on Thu Aug 15 12:45:29 2024

@author: atakan
"""

import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import carbatpy as cb

# ------- input data -----------


def heat_pump(dir_name, **kwargs):
    """
    Runs a heat pump model using configuration parameters from a YAML file or a dictionary.
    
    Uses the components defined in comp. The configuration is using two secondary
    fluids (storages), one is heated, the other one is cooled down, both starting
    at ambient temperature. The power is set in the yaml file and fixed. The starting point of the
    cycle is the state at the compressor inlet, which is superheated (by a fixed value),
    as set in the yaml file and the temperature is below the ambient temperature
    by the set dt_min value. The maximum temperature of the hot storage and the
    minimum temperature of the cold storage are set in the yaml file. The low and high 
    pressure of the working fluid are set also in the yaml file. All these values
    are the found in the configuration dictionary, which is part of the output dictionary.
    if plotting is True, a T-H_dot plot of the cycle is created.

    Parameters
    ----------
    dir_name : str or dict
        Either the path to a YAML file with all configuration parameters, or a dictionary containing them directly.
    **kwargs :
        Additional keyword arguments. Supported keys:
            config : dict, optional
                Dictionary with configuration parameters to overwrite those from dir_name (useful for optimization).
            verbose : bool, optional
                If True, enables verbose output. Default is False.
            plotting : bool, optional
                If True a T-H_dot plot of the cycle will be plotted
            ... (any other parameters can be described here)

    Returns
    -------
    cop : float
        COP of the heat pump.
    outputs: dict
        Dictionary with the output of each part and the comfiguration (input).
        
    warnings : dict
        Warning for each part
    fig : Figure matplotlib
        Access to the figure.
    ax : matplotlib axes
        Access to the axes.

    Notes
    -----
    This function can be used as an interface for both direct calculations and parameter optimization
    within the heat pump design/analysis workflow.

    Example
    -------
    >>> results = heat_pump('config.yaml', config=new_config, verbose=True)
    """
    
    new_config = kwargs.get("config", None)  # for optimizations
    verbose = kwargs.get("verbose", False)
    plotting = kwargs.get("plotting", False)
    
    fig = None
    ax = None
    warnings = {}
    outputs = {}

    def add_w_o(what):
        warnings[what.name] = what.warning
        outputs[what.name] = what.output
    # ================ CALCULATIONS ==============================
    # ------ Start/initial condition ----
    # but the mass flow rate is yet unknown, plotting must be delayed
    start = cb.comp.Start("start", dir_name, m_dot=10e-3)
    config = start.config
    if new_config is not None:
        for key in new_config:
            if key in config and isinstance(config[key], dict) and isinstance(new_config[key], dict):
                config[key].update(new_config[key])
            else:
                config[key] = new_config[key]

    start = cb.comp.Start("start", config, m_dot=10e-3)
    # ----- compressor --------------
    # prescribed power, working_fluid mass flow rate is calculated here
    try:
        power = new_config["process"]["fixed"]["compressor"]["power"]
    except:
        power = config["process"]["fixed"]["compressor"]["power"]
        
    run_p_comp = {"power": power}

    compressor = cb.comp.FlowMachine("compressor", config)
    p_high = compressor.config['working_fluid']['p_high']
    p_ratio =  p_high / start.output["state_out"][1]
    if p_ratio < 1:
        warnings["pressure_ratio"] = cb.comp.warn
        warnings["pressure_ratio"].value= 10 / p_ratio
        warnings["pressure_ratio"].message= "Pressure ratio is wrong"
        # return here? Which parameters must be set?
    compressor.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param=run_p_comp)  # ,  m_dot=10e-3)
    # for the output only p_high is used! Now m_dot is known for the working fluid.
    m_dot_w = compressor.output["m_dot"]['working_fluid']
    m_dot ={"m_dot":{"working_fluid":m_dot_w}}
    start = cb.comp.Start("start", config, m_dot=m_dot_w)
    add_w_o(start)
    add_w_o(compressor)

    # ----- coondenser --------------
    run_p_cond = {"m_dot": {"working_fluid": m_dot_w}}

    condenser = cb.comp.StaticHeatExchanger("condenser", config)
    inp1, outp1 = condenser.set_in_out(
        {'working_fluid': compressor.output['state_out']["working_fluid"]})

    condenser.calculate(in_states=inp1, run_param=run_p_cond, verbose=False)
    volumes_c = condenser.calculate_volume() #  parameters={"time": 3.6e3, "Energy_stored":3.6e6*10})
    if verbose:
        print(f'Storage Volumes condenser: {volumes_c}')
    # condenser.hex_opti_work_out(run_p_par=run_p_cond)

    # condenser.output["state_out"]["working_fluid"]
    throttle = cb.comp.Throttle("throttle", config)
    throttle.calculate(condenser.output["state_out"], #["working_fluid"],
                       compressor.output["state_in"],
                       run_param=m_dot)
    add_w_o(throttle)
    add_w_o(condenser)

    evaporator = cb.comp.StaticHeatExchanger("evaporator", config)
    inp1, outp1 = evaporator.set_in_out(
        {'working_fluid': throttle.output['state_out']["working_fluid"]})
    inp2, outp2 = evaporator.set_in_out(
        start.output['state_in'], False)
    evaporator.calculate(inp1, outp2, run_param=run_p_cond, verbose=False)
    volumes_e = evaporator.calculate_volume() #  parameters={"time": 3.6e3,"Energy_stored":3.6e6*10})
    if verbose:
        print(f'Storage Volumes evaporator: {volumes_e}')
    add_w_o(evaporator)

    cop = np.abs(condenser.output["q_dot"]/run_p_comp["power"])
    outputs["config"] = config
    if verbose:
        print(f"COP: {cop :.4f}")
    costs = cb.orc_comp.all_costs([compressor, condenser, throttle, evaporator])
    
    


    # =========== Calculations finished ====================
    # --------- plot preparation ------------
    if plotting:
        fig, ax = plt.subplots(1)
        plot_info = cb.CB_DEFAULTS["Components"]["Plot"]
        plot_info.update({"ax": ax, "fig": fig, "x-shift": [0, 0]})
    
        pl_inf = plot_info.copy()  # for the starting point (dot)
        pl_inf.update({"label": ["start", ""],
                       "col": ["ok", "bv"],
                       "direction": 1, })
        #
        #     Plotting starts
        shift, direct = start.plot(pl_inf)
    
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [compressor.name, ""],
                          "col": ["-r", "bv-"]})
        shift, direct = compressor.plot(plot_info)
    
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [condenser.name, ""],
                          "col": [":r", "rv-"]})
        shift, direct = condenser.plot(plot_info)
    
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [throttle.name, ""],
                          "col": ["-b", "bv-"]})
        shift, direct = throttle.plot(plot_info)
    
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [evaporator.name, ""],
                          "col": [":b", "bv-"]})
        evaporator.plot(plot_info)
        
    results = {"COP" : cop,
                         "output": outputs, 
                         "warnings": warnings, 
                         "figure": fig, 
                         "axes": ax,
                         "costs": costs,
                         }
    return results



if __name__ == "__main__":
    OPTI = False

    dir_name_out = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"
    #dir_name_out = r"C:\Users\atakan\sciebo\results\io-cycle-data-prop-pent.yaml"

    conf_m = {"cold_storage": {"temp_low": 274.},
              "working_fluid": {"p_high": 1.49e6,
                                'fractions': [.4, 0.4, .20, 0.0000]}}
    
    # conf = dir_name
    bounds_m = {"cold_storage": {"temp_low": [265, 277]},
                "working_fluid":
                {"p_high": [5e5, 01.8e6],
                 'fractions': [[0.0, .85], [0, 0.5], [0.0, .005], [0, 0.5]]},

                }  # for fractions only maximal values

    res_act = heat_pump(
        dir_name_out, config=conf_m, verbose=True, plotting =True)
    if any(ns.value != 0 for ns in res_act['warnings'].values()):
        print(f"Check Warnings, at least one deviates from 0!\n {res_act['warnings']}")


    # # testen:
    # x_i, bn, pa =extract_optim_data_with_paths(conf_m, bounds_m)
    # print(x_i, bn, pa )

    # print(insert_optim_data(conf_m, x_i, pa))
    # xx, co, pa =extract_optim_data_with_paths(conf_m, bounds_m)
    # print("Hier:", xx)
    # print(_opti_hp_func(xx, conf_m, dir_name_out, pa))



    if OPTI:
        # for optimization:
        how_opt = "bas_hop"
        opt_res, paths = cb.opti_cycle_comp_helpers.optimize_wf_heat_pump(dir_name_out, conf_m, bounds_m,
                                        optimize_global=how_opt)
        print(opt_res)



        if how_opt == "bas_hop":
            # Angenommen:
            # optResult.population.shape = (75, 5)
            # optResult.population_energies.shape = (75,)
    
            colnames = ["T_cold", "p_h", "propane",  "pentane", "heptane"]
            # Prüfe vorsichtshalber auf die richtige Länge:
            assert len(colnames) == opt_res.population.shape[1]
    
            df = pd.DataFrame(opt_res.population, columns=colnames)
            df["cop-weighted"] = opt_res.population_energies
    
            p_l = []
            c6 = []
            p_ratio = []
            cops = []
            for o_val in opt_res.population:
                conf_o = cb.opti_cycle_comp_helpers.insert_optim_data(conf_m, o_val, paths)
                # conf_o = {"working_fluid": {"p_high": o_val[0],  'fractions':  [
                #     *o_val[1:], 1 - np.sum(o_val[1:])]}}
                cop_o, ou_o, wa_o, fi_o, ax_o = heat_pump(
                    dir_name_out, config=conf_o, verbose=True, plotting=True)
                p_l_opt = ou_o['start']['p_low']
                p_h_opt = conf_o["working_fluid"]["p_high"]
                p_l.append(p_l_opt)
                c6.append(1-np.sum(o_val[1:]))
                p_ratio.append(p_h_opt / p_l_opt)
                cops.append(cop_o)
            df["octane"] = c6
            df["p_low"] = p_l
            df["p_ratio"] = p_ratio
            df['cop'] = cops
            df.to_csv(
                r"C:\Users\atakan\sciebo\results\optResult_368K_255K_pro_pen_Tcold.csv",
                index=False)
        else:
            o_val = opt_res.x
            cb.opti_cycle_comp_helpers.insert_optim_data(conf_m, o_val, paths)
            res_o = heat_pump(
                dir_name_out, config=conf_o, verbose=True, plotting=True)
            print(f"COP-Optimized by {how_opt}: {res_o['COP']:.2f}")
            
