# -*- coding: utf-8 -*-
"""
Heat pump with two two-tank storage, with the new component (comp.py) formulation.

Created on Thu Aug 15 12:45:29 2024

@author: atakan
"""
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, differential_evolution, basinhopping
import pandas as pd
import carbatpy as cb

# ------- input data -----------


def heat_pump(dir_name, power=1000., **kwargs):
    """
    Runs a heat pump model using configuration parameters from a YAML file or a dictionary.
    
    Uses the components defined in comp.

    Parameters
    ----------
    dir_name : str or dict
        Either the path to a YAML file with all configuration parameters, or a dictionary containing them directly.
    power : float, optional
        Compressor power [W]. The default is 1000.
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
    >>> results = heat_pump('config.yaml', power=1200., config=new_config, verbose=True)
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
    run_p_comp = {"power": power}

    compressor = cb.comp.FlowMachine("compressor", config)
    p_high = compressor.config['working_fluid']['p_high']
    compressor.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param=run_p_comp)  # ,  m_dot=10e-3)
    # for the output only p_high is used! Now m_dot is known for the working fluid.
    m_dot_w = compressor.output["m_dot"]
    start = cb.comp.Start("start", config, m_dot=m_dot_w)
    add_w_o(start)
    add_w_o(compressor)

    # ----- coondenser --------------
    run_p_cond = {"m_dot": {"working_fluid": m_dot_w}}

    condenser = cb.comp.StaticHeatExchanger("condenser", config)
    inp1, outp1 = condenser.set_in_out(
        {'working_fluid': compressor.output['state_out']["working_fluid"]})

    condenser.calculate(in_states=inp1, run_param=run_p_cond, verbose=False)
    # condenser.hex_opti_work_out(run_p_par=run_p_cond)

    # condenser.output["state_out"]["working_fluid"]
    throttle = cb.comp.Throttle("throttle", config)
    throttle.calculate(condenser.output["state_out"]["working_fluid"],
                       compressor.output["state_in"],
                       m_dot=m_dot_w)
    add_w_o(throttle)
    add_w_o(condenser)

    evaporator = cb.comp.StaticHeatExchanger("evaporator", config)
    inp1, outp1 = evaporator.set_in_out(
        {'working_fluid': throttle.output['state_out']["working_fluid"]})
    inp2, outp2 = evaporator.set_in_out(
        start.output['state_in'], False)
    evaporator.calculate(inp1, outp2, run_param=run_p_cond, verbose=False)
    add_w_o(evaporator)

    cop = np.abs(condenser.output["q_dot"]/run_p_comp["power"])
    outputs["config"] = config
    if verbose:
        print(f"COP: {cop :.4f}")

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
    return cop, outputs, warnings, fig, ax


def optimize_wf_heat_pump(dir_name, config_0, bounds_0, **kwargs):
    """
    Heat pump COP optimization, varying p_high and mixture composition

    p_low cannot be selected directly, it is determined by the storage
    temperature and the superheating temperature difference and the minimum
    approach temperature. In optimization, the low pressure (wanted) from
    the conciguration yaml file is checked. If the calculated low pressure is
    below that value, the COP is weighted with the ratio.

    Parameters
    ----------
    dir_name : str or dict
        either the path to the yaml file with all configuration parameters, or
        a dictionary with all values.
    config_0 : dict
        vales set here and deviating from dir_name.
    bounds_0 : dictTYPE
        dictionary with the p_high bounds and the upper bounds of the first
        three molefractions. The remaining value is the difference to 1. It is
        checked that the sum is 1 and all vales are positive.

    **kwargs :
        - 'optimize_global': select optimization algorith "dif_evol", "bas_hop",
        or local minimizer (Nelson Mead).

    Returns
    -------
    result : OptimizeResult
        The result of the optimization.
    paths: list of lists
        from function extract_optim_data_with_paths. Needed to reconstruct the
        config_0 dictionary from the optimizer x-list.

    """

    x0, bnds, paths = extract_optim_data_with_paths(config_0, bounds_0)
    opt_global = kwargs.get('optimize_global', "dif_evol")
    tolerance = 1e-4
    max_iter = 320

    if opt_global == "dif_evol":
        result = differential_evolution(_opti_hp_func,
                                        bnds,
                                        args=(config_0, dir_name, paths),
                                        workers=3,
                                        maxiter=max_iter,
                                        )
    elif opt_global == "bas_hop":
        result = basinhopping(_opti_hp_func,
                              x0,
                              minimizer_kwargs={'method': 'Nelder-Mead',
                                                'bounds': bnds,
                                                'args': (config_0,
                                                         dir_name,
                                                         paths)},
                              )
    else:
        # Local optimization
        result = minimize(_opti_hp_func,
                          x0,
                          args=(config_0, dir_name, paths),
                          method='Nelder-Mead',
                          # tol=tolerance,
                          bounds=bnds,
                          # constraints=cons,
                          options={
                              # 'finite_diff_rel_step': .05,
                              "maxiter": max_iter,  # can take long!
                              "disp": True})
    return result, paths


def _opti_hp_func(x,  conf, dir_name, paths, verbose=False, **kwargs):
    """
    Function for heat pump optimization, p_high and 4-component mixture

    Parameters
    ----------
    x : array/list, length 4
        p_high and the first three mole fractions.
    conf :  dict
        vales set here and deviating from dir_name.
    dir_name : str or dict
        either the path to the yaml file with all configuration parameters, or
        a dictionary with all values.
    paths: list of lists
        from function extract_optim_data_with_paths. Needed to reconstruct the
        config_0 dictionary from the optimizer x-list.
    verbose : TYPE, optional
        DESCRIPTION. The default is False.
    **kwargs : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    # conf_act = {"working_fluid": {}}

    # for ii, key in enumerate(conf["working_fluid"].keys()):

    #     if key == "fractions":
    #         n_sp = len(conf["working_fluid"]["fractions"])
    #         fractions = []
    #         x_tot = 0
    #         for nf in range(n_sp - 1):
    #             x_act = x[ii+nf]
    #             fractions.append(x_act)
    #             x_tot += x_act
    #         fractions.append(1 - x_tot)
    #         conf_act["working_fluid"]["fractions"] = fractions

    #     else:
    #         conf_act["working_fluid"][key] = x[ii]
    conf_act = insert_optim_data(conf, x, paths)
    if any(np.array(x) < 0):
        return 500

    try:
        cop, ou, wa, fi, ax = heat_pump(dir_name, config=conf_act)

        p_low_actual = ou["start"]["p_low"]
        p_low_min = ou['config']['working_fluid']["p_low"]
        p_l_ratio = p_low_actual / p_low_min
        factor = 1
        if p_l_ratio <= 1:  # punish too low pressures
            factor = p_l_ratio
        if verbose:
            print(cop, wa, x, 1-np.sum(x[1:]), factor, "\n", conf_act)

    except:
        return 509
    if any(ns.value >= 10 for ns in wa.values()):
        return 100 * cop
    return -cop * factor


def extract_optim_data(conf, bounds):  # will be removed
    # should perhaps also  be generlized for upper level keys
    wf_conf = conf["working_fluid"]
    wf_bounds = bounds["working_fluid"]

    x0 = []
    bnds = []
    """
    MUSS integriert werden BA 2025-08-02
    for key in new_config:
    if key in config and isinstance(config[key], dict) and isinstance(new_config[key], dict):
        config[key].update(new_config[key])
    else:
        config[key] = new_config[key]

    """
    for key, val in wf_conf.items():
        if key == "fractions":
            for ii, x_i in enumerate(val[:-1]):
                x0.append(x_i)
                bnds.append(tuple(wf_bounds["fractions"][ii]))
        else:
            x0.append(val)
            bnds.append((tuple(wf_bounds[key])))

    # x0 = [
    #     wf_conf["p_high"],
    #     *wf_conf["fractions"][:3]
    # ]

    # bnds = [
    #     tuple(wf_bounds["p_high"]),
    #     (0.0, wf_bounds["fractions"][0]),
    #     (0.0, wf_bounds["fractions"][1]),
    #     (0.0, wf_bounds["fractions"][2]),
    # ]

    # f4max = wf_bounds["fractions"][2]
    # # 1. fraction_4 \>= 0: x[2] + x[3] + x[4] \<= 1
    # # 2. fraction_4 <= f4max: x[2] + x[3] + x[4] \>= 1 - f4max

    # cons = [
    #     {'type': 'ineq', 'fun': lambda x:  1 -
    #         (x[2] + x[3] + x[1])},        # \<=1
    #     {'type': 'ineq', 'fun': lambda x:  (
    #         x[2] + x[3] + x[1]) - (1 - f4max)},  # \>=1-f4max
    # ]
    return x0, bnds  # , cons

def extract_optim_data_with_paths(config, bounds):
    """
    Extracts all optimizable parameter values, along with their bounds and hierarchical paths,
    from a (possibly nested) configuration dictionary for optimization (e.g., heat pump application).

    Parameters
    ----------
    config : dict
        The (possibly nested) configuration dictionary containing initial values.
    bounds : dict
        Dictionary with bounds for all optimizable parameters, structured like config.

    Returns
    -------
    x0 : list
        A flat list of all initial parameter values to be optimized (e.g., p_high and mole fractions).
    bnds : list
        List of bounds tuples corresponding to all entries in x0.
    paths : list of lists
        Each entry is the hierarchical path (list of keys/indices) to the corresponding variable in config.
        Can be used to reconstruct the config dictionary from an x-list after optimization.

    Example
    -------
    >>> x0, bnds, paths = extract_optim_data_with_paths(config, bounds)
    """
    x0 = []
    bnds = []
    paths = []
    def _extract(conf_level, bounds_level, path):
        for key, val in conf_level.items():
            if key not in bounds_level:
                continue
            if isinstance(val, dict) and isinstance(bounds_level[key], dict):
                _extract(val, bounds_level[key], path + [key])
            elif key == "fractions":
                for ii, x_i in enumerate(val[:-1]):
                    x0.append(x_i)
                    bnds.append(tuple(bounds_level["fractions"][ii]))
                    paths.append(path + [key, ii])
            else:
                x0.append(val)
                bnds.append(tuple(bounds_level[key]))
                paths.append(path + [key])
    _extract(config, bounds, [])
    return x0, bnds, paths


def insert_optim_data(config, x, paths):

    """
    Reconstructs a configuration dictionary from a flat list of optimized values
    and corresponding paths, including special handling for mole fractions.
    For back conversion after optimization (scipy.optimize).

    Parameters
    ----------
    config : dict
        The original configuration dictionary (will be deep-copied).
    x : list or array
        The optimizer parameter vector (e.g., for p_high and first n-1 mole fractions).
    paths : list of lists
        The list of hierarchical paths as produced by extract_optim_data_with_paths;
        describes where in config each value from x should be inserted.

    Returns
    -------
    conf_new : dict
        A new dictionary with the updated parameter values from x inserted.
        For fields called 'fractions', the last value is set to 1 minus the sum
        of the others (to ensure the fractions sum to 1).

    Example
    -------
    >>> conf_new = insert_optim_data(config, x, paths)
    """

    conf_new = deepcopy(config)
    fractions_groups = {}  # Key: Pfad bis 'fractions', Value: Liste von (Pfad, x-Index)
    for i, path in enumerate(paths):
        if len(path) >= 2 and path[-2] == "fractions":
            grp = tuple(path[:-2])  # Neu: bis VOR 'fractions' (also z.B. ["working_fluid"])
            if grp not in fractions_groups:
                fractions_groups[grp] = []
            fractions_groups[grp].append((path, i))

    # Normale Parameter
    for val, path in zip(x, paths):
        if len(path) >= 2 and path[-2] == "fractions":
            continue  # fractions werden gesammelt behandelt
        conf_level = conf_new
        for p in path[:-1]:
            conf_level = conf_level[p]
        conf_level[path[-1]] = val

    # fractions-Gruppen: Korrigierter Zugriff
    for grp, path_indices in fractions_groups.items():
        # n-1 optimierbare Fraktionen stehen im Pfad
        group_length = len(path_indices) + 1
        fraction_values = [x[idx] for _, idx in sorted(path_indices, key=lambda xx: xx[0][-1])]
        last_val = 1.0 - sum(fraction_values)
        full_fractions = fraction_values + [last_val]
        # Zugriff bis zum richtigen dict
        conf_level = conf_new
        for p in grp:
            conf_level = conf_level[p]
        conf_level["fractions"] = full_fractions

    return conf_new


if __name__ == "__main__":
    OPTI = False

    dir_name_out = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"
    dir_name_out = r"C:\Users\atakan\sciebo\results\io-cycle-data-prop-pent.yaml"

    conf_m = {"working_fluid": {"p_high": 1.29e6,
                                'fractions': [.55, 0.35, .05, 0.050]}}
    conf_m = {"cold_storage": {"temp_low": 275.},
              "working_fluid": {"p_high": 1.e6,
                                'fractions': [0.75,
                                              0.25,
                                              0.01e-4,
                                              0.01e-4]},
              }
    # conf = dir_name
    bounds_m = {"cold_storage": {"temp_low": [265, 277]},
                "working_fluid":
                {"p_high": [5e5, 01.8e6],
                 'fractions': [[0.0, .85], [0, 0.5], [0.0, .005], [0, 0.5]]},

                }  # for fractions only maximal values

    cop_m, ou_m, wa_m, fi_m, ax_m = heat_pump(
        dir_name_out, config=conf_m, verbose=True, plotting =True)
    if any(ns.value != 0 for ns in wa_m.values()):
        print(f"Check Warnings, at least one deviates from 0!\n {wa_m}")


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
        opt_res, paths = optimize_wf_heat_pump(dir_name_out, conf_m, bounds_m,
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
                conf_o = insert_optim_data(conf_m, o_val, paths)
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
            insert_optim_data(conf_m, o_val, paths)
            cop_o, ou_o, wa_o, fi_o, ax_o = heat_pump(
                dir_name_out, config=conf_o, verbose=True, plotting=True)
            print(f"COP-Optimized by {how_opt}: {cop_o:.2f}")
            
