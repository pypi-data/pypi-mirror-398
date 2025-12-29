# -*- coding: utf-8 -*-
"""

Helper functions for optimizations of cycles, which use comp.py.

Created on Mon Aug  4 11:39:05 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""
from copy import deepcopy
import multiprocessing
import gc
import numpy as np
from scipy.optimize import minimize, differential_evolution, basinhopping, shgo
import carbatpy as cb


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
        'shgo', or local minimizer (Nelson Mead).

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
    max_iter = kwargs.get('maxiter', 200)
    workers = kwargs.get('workers', 1)
    opt_options =kwargs.get('opt_options',{})
    tolerance = 1e-4

    if opt_global == "dif_evol":
        result = differential_evolution(_opti_hp_func,
                                        bnds,
                                        args=(config_0,
                                              dir_name, paths),
                                        workers=workers,
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
    elif opt_global == "shgo":
        result = shgo(_opti_hp_func,
                      bounds=bnds,
                      args=(config_0, dir_name, paths),
                      minimizer_kwargs={'method': 'Nelder-Mead', },
                      workers=workers,
                      options=opt_options,
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


def _opti_hp_func(x, conf, dir_name, paths, verbose=True, **kwargs):
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

    conf_act = insert_optim_data(conf, x, paths)
    if "fractions" in conf_act["working_fluid"].keys():
        if conf_act["working_fluid"]["fractions"][-1] < 0:
            return -conf_act["working_fluid"]["fractions"][-1] * 10
    xn = np.array(x)
    if any(xn < 0):
        return - xn[xn < 0].sum() * 10

    try:
        hp_res = cb.hp_comp.heat_pump(dir_name,
                                      config=conf_act,
                                      verbose=verbose)

        p_low_actual = hp_res['output']["start"]["p_low"]
        p_low_min = hp_res['output']['config']['working_fluid']["p_low"]
        p_l_ratio = p_low_actual / p_low_min
        factor = 1
        if p_l_ratio <= 1:  # punish too low pressures
            factor = p_l_ratio * -10
        if verbose:
            for key, w_act  in hp_res['warnings'].items():
                if w_act.value  >0:
                    print(key,w_act, x)

    except Exception as e:
        print("Fehler aufgetreten:", type(e), e)
        return 5.9
    if any(ns.value > 0 for ns in hp_res['warnings'].values()):
        return sum(item.value for item in hp_res['warnings'].values())
    return -hp_res['COP'] * factor


# -------- ORC ------------------

def optimize_orc(dir_name, cop, q_dot_h, config_0, bounds_0, **kwargs):
    """
    ORC optimization, varying p_high and mixture composition etc.



    Parameters
    ----------
    dir_name : str or dict
        either the path to the yaml file with all configuration parameters, or
        a dictionary with all values.
    cop : float
        COP of the charging heat pump; is needed to secure steady state
        discharging.
    q_dot_h : float
        The heat flow from the high temperature storage to the working fluid
        in the evaporator.
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
    max_iter = kwargs.get('maxiter', 200)
    workers = kwargs.get('workers', 1)
    opt_options =kwargs.get('opt_options',{})
    tolerance = 1e-4

    if opt_global == "dif_evol":

        result = differential_evolution(_opti_orc_func,
                                        bnds,
                                        args=(cop, q_dot_h, config_0,
                                              dir_name, paths),
                                        workers=workers,
                                        maxiter=max_iter,
                                        )
    elif opt_global == "bas_hop":
        result = basinhopping(_opti_orc_func,
                              x0,
                              minimizer_kwargs={'method': 'Nelder-Mead',
                                                'bounds': bnds,
                                                'args': (cop, q_dot_h, config_0,
                                                         dir_name,
                                                         paths)},
                              )
    elif opt_global == "shgo":
        result = shgo(_opti_orc_func,
                      bounds=bnds,
                      args=(cop, q_dot_h, config_0, dir_name, paths),
                      minimizer_kwargs={'method': 'Nelder-Mead',
                                        },
                      workers=workers,
                      options=opt_options,
                      )
    else:
        # Local optimization
        result = minimize(_opti_orc_func,
                          x0,
                          args=(cop, q_dot_h, config_0, dir_name, paths),
                          method='Nelder-Mead',
                          # tol=tolerance,
                          bounds=bnds,
                          # constraints=cons,
                          options={
                              # 'finite_diff_rel_step': .05,
                              "maxiter": max_iter,  # can take long!
                              "disp": True})
    return result, paths


def _opti_orc_func(x, cop, q_dot_h, conf, dir_name, paths, verbose=False, **kwargs):
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

    conf_act = insert_optim_data(conf, x, paths)
    if "fractions" in conf_act["working_fluid"].keys():
        if conf_act["working_fluid"]["fractions"][-1] < 0:
            return -conf_act["working_fluid"]["fractions"][-1] * 10
    xn = np.array(x)
    if any(xn < 0):
        return - xn[xn < 0].sum() * 10

    # try:
    res_orc = cb.orc_comp.orc(dir_name, cop, q_dot_h,
                              config=conf_act)

    if verbose:
        print(res_orc["eta_th"], "\n", res_orc['warnings'], "\n", conf_act)

    # except Exception as e:
    #     print("Fehler aufgetreten:", type(e), e)
        return 5.09
    if res_orc["eta_th"] < 0:
        return - res_orc["eta"] * 10.00
    elif any(ns.value > 0 for ns in res_orc['warnings'].values()):
        return sum(item.value for item in res_orc['warnings'].values())

    return -res_orc["eta_th"]

# ---------------------------------------------------------------
# ------------------Carnot Battery/PTES -------------------------


def optimize_cb(dir_names, configs, bounds, **kwargs):
    """
    CB optimization, varying p_high and mixture composition etc.



    Parameters
    ----------
    dir_name : str or dict
        either the path to the yaml file with all configuration parameters, or
        a dictionary with all values.
    cop : float
        COP of the charging heat pump; is needed to secure steady state
        discharging.
    q_dot_h : float
        The heat flow from the high temperature storage to the working fluid
        in the evaporator.
    config_0 : dict
        vales set here and deviating from dir_name.
    bounds_0 : dictTYPE
        dictionary with the p_high bounds and the upper bounds of the first
        three molefractions. The remaining value is the difference to 1. It is
        checked that the sum is 1 and all vales are positive.

    **kwargs :
        - 'optimize_global': select optimization algorith "dif_evol", "bas_hop",
        or local minimizer (Nelson Mead).
        - 'workers': the number of workers for the differential evolution algorithm.
        Integer, optional, default value is 1.
        - 'maxiter': maximum iterations of optimizers, integer, default value is 200.

    Returns
    -------
    result : OptimizeResult
        The result of the optimization.
    paths: list of lists
        from function extract_optim_data_with_paths. Needed to reconstruct the
        config_0 dictionary from the optimizer x-list.

    """
    x = {}
    bnds = {}
    paths = {}

    x0 = []
    bnds_tot = []
    for key in ["hp", "orc"]:
        x[key], bnds[key], paths[key] = extract_optim_data_with_paths(
            configs[key], bounds[key])
        x0 += x[key]
        bnds_tot += bnds[key]

    opt_global = kwargs.get('optimize_global', "dif_evol")

    max_iter = kwargs.get('maxiter', 200)
    workers = kwargs.get('workers', 1)
    opt_options =kwargs.get('opt_options',{})
    args_act = (configs, dir_names, paths)

    if opt_global == "dif_evol":

        result = differential_evolution(_opti_cb_func,
                                        bnds_tot,
                                        args=args_act,
                                        workers=workers,
                                        maxiter=max_iter,
                                        x0=x0,
                                        )
    elif opt_global == "bas_hop":
        result = basinhopping(_opti_cb_func,
                              x0,
                              minimizer_kwargs={'method': 'Nelder-Mead',
                                                'bounds': bnds_tot,
                                                'args': args_act},
                              )
    elif opt_global == "shgo":
        result = shgo(_opti_cb_func,
                      bounds=bnds_tot,
                      args=args_act,
                      #minimizer_kwargs={'method': 'Nelder-Mead',},
                      workers=workers,
                      options=opt_options,
                      n = 999,
                      #sampling_method='sobol',
                      )
    else:
        # Local optimization
        result = minimize(_opti_cb_func,
                          x0,
                          args=args_act,
                          method='Nelder-Mead',
                          # tol=tolerance,
                          bounds=bnds_tot,
                          # constraints=cons,
                          options={
                              # 'finite_diff_rel_step': .05,
                              "maxiter": max_iter,  # can take long!
                              "disp": True})

    gc.collect()
    multiprocessing.active_children()  # leere Liste -> keine offenen Prozesse mehr?
    return result, paths


def _opti_cb_func(x, configs, dir_names, paths, verbose=False, **kwargs):
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
    conf_act = {}

    for key in configs.keys():
        match key:
            case "hp":
                x_k = x[:len(paths["hp"])]
            case "orc":
                x_k = x[len(paths["hp"]):]
        conf_act[key] = insert_optim_data(configs[key], x_k, paths[key])
        if key == "hp" and conf_act[key]["working_fluid"]["fractions"][-1] < 0:
            return -conf_act[key]["working_fluid"]["fractions"][-1] * 10
    xn = np.array(x)
    if any(xn < 0):
        return - xn[xn < 0].sum() * 10

    try:
        rte, result = cb.cb_comp.cb_calc(dir_names,
                                         config=conf_act)

        if verbose:
            print(rte, "\n")

    except Exception as e:
        print("Fehler aufgetreten:", type(e), e)
        return 0.9
    if rte < 0:
        return -rte * 10.0

    return -rte

# --------------------------------------------------------


def extract_cb_conf_from_x(x, configs_ini, paths):
    conf_act = {}

    for key in configs_ini.keys():
        match key:
            case "hp":
                x_k = x[:len(paths["hp"])]
            case "orc":
                x_k = x[len(paths["hp"]):]

        conf_act[key] = insert_optim_data(configs_ini[key], x_k, paths[key])

    return conf_act




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

# ---------------------------------------------------------------


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
    # Key: Pfad bis 'fractions', Value: Liste von (Pfad, x-Index)
    fractions_groups = {}
    for i, path in enumerate(paths):
        if len(path) >= 2 and path[-2] == "fractions":
            # Neu: bis VOR 'fractions' (also z.B. ["working_fluid"])
            grp = tuple(path[:-2])
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
        # n-1 optimierbare mole fractions stehen im Pfad
        group_length = len(path_indices) + 1
        fraction_values = [x[idx] for _, idx in sorted(
            path_indices, key=lambda xx: xx[0][-1])]
        last_val = 1.0 - sum(fraction_values)
        full_fractions = fraction_values + [last_val]
        # Zugriff bis zum richtigen dict
        conf_level = conf_new
        for p in grp:
            conf_level = conf_level[p]
        conf_level["fractions"] = full_fractions

    return conf_new


def parse_species_string(species_str):
    """
    Converts a species string in format 'Propane * Butane * Pentane * Hexane'
    into a list without spaces and asterisks.

    Parameters
    ----------
    species_str : str
        Species string with asterisk separation

    Returns
    -------
    list
        List of species names
    """
    if isinstance(species_str, str):
        return [species.strip() for species in species_str.split('*')]
    return species_str  # If already a list


def extract_cycle_column_names_from_config(config_dict, paths):
    """
    Extracts column names for optimization variables based on paths.
    Returns a single flat list with prefixed names for non-fraction variables.

    Parameters
    ----------
    config_dict : dict
        Dictionary with configuration data (contains species names for fractions)
        Structure: config_dict["working_fluid"]["species"] = "Propane * Butane * ..."
    paths : list
        Dictionary with paths for each optimization 

    Returns
    -------
    list
        Single flat list of column names for all optimization variables
    """
    all_names = []

    
    for path in paths:
        if len(path) >= 2 and path[-2] == "fractions":
            # For fractions: Extract species names from config_dict (no prefix)
            # Find the working_fluid section that contains the species
            species_list = None

            # Look for species in the path hierarchy (usually under working_fluid)
            for key in path[:-2]:  # Go through path up to 'fractions'
                if key == "working_fluid" and "working_fluid" in config_dict:
                    if "species" in config_dict["working_fluid"]:
                        species_list = parse_species_string(
                            config_dict["working_fluid"]["species"])
                        break

            # If species found, use species name, otherwise use generic name
            if species_list:
                fraction_idx = path[-1]
                if fraction_idx < len(species_list):
                    all_names.append(
                        f"{species_list[fraction_idx]}_fraction")
                else:
                    all_names.append(f"fraction_{fraction_idx}")
            else:
                all_names.append(f"fraction_{path[-1]}")
        else:
            # For normal parameters: Use group prefix + parameter name
            all_names.append(f"{path[-1]}")

    return all_names



def extract_column_names_from_config(config_dict, paths_dict):
    """
    Extracts column names for optimization variables based on paths.
    Returns a single flat list with prefixed names for non-fraction variables.

    Parameters
    ----------
    config_dict : dict
        Dictionary with configuration data (contains species names for fractions)
        Structure: config_dict["working_fluid"]["species"] = "Propane * Butane * ..."
    paths_dict : dict
        Dictionary with paths for each optimization group (e.g. "hp", "orc")

    Returns
    -------
    list
        Single flat list of column names for all optimization variables
    """
    all_names = []

    for group_key, paths in paths_dict.items():
        for path in paths:
            if len(path) >= 2 and path[-2] == "fractions":
                # For fractions: Extract species names from config_dict (no prefix)
                # Find the working_fluid section that contains the species
                species_list = None

                # Look for species in the path hierarchy (usually under working_fluid)
                for key in path[:-2]:  # Go through path up to 'fractions'
                    if key == "working_fluid" and "working_fluid" in config_dict:
                        if "species" in config_dict["working_fluid"]:
                            species_list = parse_species_string(
                                config_dict["working_fluid"]["species"])
                            break

                # If species found, use species name, otherwise use generic name
                if species_list:
                    fraction_idx = path[-1]
                    if fraction_idx < len(species_list):
                        all_names.append(
                            f"{species_list[fraction_idx]}_fraction")
                    else:
                        all_names.append(f"fraction_{fraction_idx}")
                else:
                    all_names.append(f"fraction_{path[-1]}")
            else:
                # For normal parameters: Use group prefix + parameter name
                all_names.append(f"{group_key}_{path[-1]}")

    return all_names