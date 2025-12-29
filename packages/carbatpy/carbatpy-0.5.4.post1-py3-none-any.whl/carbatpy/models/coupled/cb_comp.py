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


def cb_calc(dir_names,  **kwargs):
    """
    Runs a Carnot battery model by sequentially simulating a heat pump and an Organic Rankine Cycle (ORC)
    using the provided configuration files or dictionaries.

    The function first executes the heat pump cycle based on the configuration in `dir_names["hp"]`.
    If successful and without warnings, it extracts the relevant thermodynamic conditions and storage states
    to configure and launch the subsequent ORC calculation (using `dir_names["orc"]`).
    Both cycles may accept additional configuration dictionaries (useful for parameter optimization).
    If `plotting` is True, figures for both cycles are generated.

    The overall Carnot battery round-trip efficiency (`rte`) is computed as the product of the heat pump COP
    and the ORC thermal efficiency.

    Parameters
    ----------
    dir_names : dict
        A dictionary with keys "hp" (for heat pump) and "orc" (for ORC), each containing
        either the path to a YAML (or similar) configuration file or a configuration dictionary.
    **kwargs :
        Additional keyword arguments. Supported keys:
            config : dict, optional
                Dictionary with additional or overriding configuration for the heat pump (`"hp"`) and/or ORC (`"orc"`)
                in the form {"hp": config_hp_dict, "orc": config_orc_dict}. Useful for optimization or parameter studies.
            verbose : bool, optional
                If True, enables verbose output. Default is False.
            plotting : bool, optional
                If True, generates diagrams for both the heat pump and ORC cycles.

    Returns
    -------
    rte : float
        The round-trip efficiency of the Carnot battery (heat pump COP × ORC thermal efficiency);
        returns negative values if warnings occur.
    results : dict
        A dictionary with two entries:
            "hp"  : results {COP, outputs_hp, warnings_hp, fig_hp, ax_hp}
            "orc" : results {eta_th, outputs_orc, warnings_orc, fig_orc, ax_orc}
        Each tuple contains the cycle performance metric, outputs, component warnings, and (optionally) plots.

    Notes
    -----
    This function calls both the heat pump and ORC functions in sequence, using outputs from the heat pump
    (such as working fluid composition and storage temperatures) to configure the ORC run. It is suitable 
    for integrating the full Carnot battery workflow, either for direct calculations, sensitivity studies, 
    or optimization routines.

    If component warnings deviate from zero for either cycle, the function will print diagnostic messages
    (if `verbose` is True) and return a negative code for `rte`.

    Example
    -------
    >>> dir_names = {"hp": "heat_pump_config.yaml", "orc": "orc_config.yaml"}
    >>> rte, results = cb_calc(dir_names, config={"hp": hp_opt_config, "orc": orc_opt_config}, plotting=True)
    """
    new_config = kwargs.get(
        "config", {"hp": None, "orc": None})  # for optimizations
    verbose = kwargs.get("verbose", False)
    plotting = kwargs.get("plotting", False)
    results = {}

    results["hp"] = cb.hp_comp.heat_pump(
        dir_names["hp"], config=new_config["hp"], verbose=verbose, plotting=plotting)
    

    if any(ns.value != 0 for ns in results["hp"]["warnings" ].values()):
        if verbose:
            print(f"Check HP Warnings, at least one deviates from 0!\n {results['hp']['warnings' ]}")
        return -sum(item.value for item in results["hp"]["warnings" ].values()), results

    # print(f"COP: {cop_h:.3f}")
    q_h = -results["hp"]["output" ]["condenser"]["q_dot"]
    
    # same fluid, same storage temperatures:
    orc_config = cb.utils.io_utils.read_config(dir_names["orc"])
    from_hp_config = {"working_fluid": {"fractions": results["hp"]["output" ]["config"]["working_fluid"]["fractions"],
                                        "species": results["hp"]["output" ]["config"]["working_fluid"]["species"]},
                      "cold_storage":  {"temp_low": results["hp"]["output" ]["config"]["cold_storage"]["temp_low"]},
                      "hot_storage": {"temp_high": results["hp"]["output" ]["config"]["hot_storage"]["temp_high"]}}
    for key in from_hp_config:
        if key in orc_config:
            orc_config[key].update(from_hp_config[key])
        else:
            orc_config[key] = from_hp_config[key]
    results["orc"] = cb.orc_comp.orc(orc_config,
                                                   results["hp"]["COP" ],
                                                   q_h,
                                                   config=new_config["orc"],
                                                   plotting=plotting)
    
    if any(ns.value != 0 for ns in results["orc"]['warnings'].values()):
        if verbose:
            print(f'Check ORC Warnings, at least one deviates from 0!\n {results["orc"]["warnings"]}')
        return -sum(item.value for item in results["orc"]['warnings'].values()), results
    rte = results["orc"]['eta_th']*results['hp']['COP']
    print(f"COP: {results['hp']['COP' ]:.3f}, eta: {results['orc']['eta_th']:.3f}, rte: {rte:.3f}")
    return rte, results


if __name__ == "__main__":
    dir_names_both = {"hp": cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml",
                      "orc": cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-orc-data.yaml"}
    rte, results_o = cb_calc(dir_names_both, plotting=True, verbose=True)
    print(f"RTE: {rte:.3f}\nHP, ORC",
          results_o["hp"]['warnings'],
          results_o["orc"]['warnings'])
