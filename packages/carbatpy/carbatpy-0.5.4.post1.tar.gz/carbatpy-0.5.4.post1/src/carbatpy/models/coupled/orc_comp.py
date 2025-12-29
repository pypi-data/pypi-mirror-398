# -*- coding: utf-8 -*-
"""
Heat pump with two two-tank storage, with the new component (comp.py) formulation.

Created on Thu Aug 15 12:45:29 2024

@author: atakan
"""
import numpy as np
import matplotlib.pyplot as plt
import carbatpy as cb

# ------- input data -----------
def orc(dir_name, cop, q_dot_high, **kwargs):
    """
   Runs an Organic Rankine Cycle (ORC) model (as part of a Carnot Battery) using configuration parameters from a YAML file or a dictionary.

   The working fluid circuit is defined using the configuration. The evaporator heat input (`q_dot_high`) and 
   the charging heat pump COP (Coefficient of Performance) are prescribed, to achieve the same state after charging and discharging. 
   The  working fluid mass flow rate is automatically determined
   based on these inputs. Cycle components considered include pump, evaporator, expander, condenser, and an 
   intermediate condenser to the surroundings, which is important for Carnot Batteries with roundtrip efficiencies below 1.
   All operational pressures and fluid properties are specified in the configuration.
   If `plotting` is True, a cycle diagram (T-H_dot or similar) is generated.

   Parameters
   ----------
   dir_name : str or dict
       Either the path to a YAML file with all configuration parameters, or a dictionary containing them directly.
   cop : float
        Coefficient of Performance (ratio of useful heat supplied to the input heat) of the charging heat pump.
   q_dot_high : float
       Prescribed heat flow rate input to the evaporator [W].
   **kwargs :
       Additional keyword arguments. Supported keys:
           config : dict, optional
               Dictionary with configuration parameters to overwrite those from dir_name (useful for optimization).
           verbose : bool, optional
               If True, enables verbose output. Default is False.
           plotting : bool, optional
               If True, generates a cycle plot.
           ... (other parameters can be specified here as needed)

   Returns
   -------
   results: dict
     Keys:
       eta_th : float
           Thermal efficiency of the ORC (ratio of net power output to heat flow rate input).
       outputs : dict
           Dictionary with the output for each component and the configuration (input).
       warnings : dict
           Dictionary with warnings for each component.
       fig : Figure, optional
           Matplotlib Figure object that holds the plot (if `plotting` is True).
       ax : matplotlib.axes.Axes, optional
           Matplotlib Axes object for the plot.

   Notes
   -----
   This function can be used as a general interface for both direct cycle calculations and parameter optimization
   within the ORC simulation/design workflow. For the latter config can be used.
   All (other) main fluid and process parameters are passed internally and/or obtained 
   from the configuration structure.

   Example
   -------
   >>> eta, results, warnings, fig, ax = orc('orc_config.yaml', cop=5, q_dot_high=2000., config=new_config, plotting=True)
   """
    new_config = kwargs.get("config", None)  # for optimizations
    verbose = kwargs.get("verbose", False)
    plotting = kwargs.get("plotting", False)
    fig = None
    ax = None
    
    warnings={}
    outputs ={}
    def add_w_o(what):
         warnings[what.name]= what.warning
         outputs[what.name ] = what.output
         
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
    p_low = start.config['working_fluid']['p_low']
    
    

    # prescribed power, working_fluid mass flow rate is calculated here
    run_p_comp = {"m_dot": 1.}
    run_p_evap = {"q_dot": q_dot_high}
    q_dot_l = - q_dot_high*(1 - 1/cop)
    run_p_cond = {"q_dot": q_dot_l}
    # ----- pump --------------
    pump = cb.comp.FlowMachine("pump", config)
    p_high = config['working_fluid']['p_high']
    p_ratio =  p_high / start.output["state_out"][1]
    if p_ratio < 1:
        warnings["pressure_ratio"] = cb.comp.warn
        warnings["pressure_ratio"].value= 10 / p_ratio
        warnings["pressure_ratio"].message= "Pressure ratio is wrong"
        # return here? Which parameters must be set?
    pump.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param={"m_dot": {'working_fluid':1.}})  # ,  m_dot=10e-3)
    # for the output only p_high is used!  m_dot for the working fluid is calculated later for the evaporator.
    
    evaporator = cb.comp.StaticHeatExchanger("evaporator", config)
    #evaporator.inputs["parameters"]['q_dot']=q_dot_high
    inp1, outp_x = evaporator.set_in_out(
        {'working_fluid': pump.output['state_out']["working_fluid"]})
    evaporator.calculate( inp1, run_param=run_p_evap, verbose=verbose)
    
    volumes_e = evaporator.calculate_volume()
    add_w_o(evaporator)
    m_dot_w = evaporator.output["m_dot"]['working_fluid']
    start = cb.comp.Start("start", config, m_dot=m_dot_w)
    run_p_machine = {"m_dot": {"working_fluid":m_dot_w}}
    pump.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param=run_p_machine, m_dot =m_dot_w)
    
    add_w_o(start)
    add_w_o(pump)
    
    # ----- expander ----------------
    expander = cb.comp.FlowMachine("expander", config)
    
    inp1 = evaporator.output['state_out']
    expander.calculate(inp1,
                         {'working_fluid': [600, p_low, 5e5]},m_dot =m_dot_w,
                         run_param=run_p_machine,
                         verbose=verbose)
    add_w_o(expander)
    power_tot = expander.output['power'] + pump.output['power']
    q_dot_sur = -(q_dot_high + q_dot_l + power_tot) # correct sign
    # ----- coondenser surrounding --------------
    run_p_cond_sur= {"q_dot": -q_dot_sur, "m_dot":  {"working_fluid": m_dot_w}}
   
    condenser_sur = cb.comp.StaticHeatExchanger("condenser_sur", config)
    inp_cs, outp_cs = condenser_sur.set_in_out(
        {'working_fluid': expander.output['state_out']["working_fluid"]})
    
    condenser_sur.calculate(inp_cs, run_param=run_p_cond_sur, verbose=verbose)
    add_w_o(condenser_sur)
    
    # ----- coondenser --------------
    run_p_cond.update( {"q_dot": -q_dot_l, "m_dot": {"working_fluid": m_dot_w}})
    
   
    condenser = cb.comp.StaticHeatExchanger("condenser", config)
    inp_c, outp_c = condenser.set_in_out(
        {'working_fluid': condenser_sur.output['state_out']["working_fluid"]})
    in_c, outp_c =  condenser.set_in_out(
        {'working_fluid': start.output['state_in']["working_fluid"]}, False)
    
    condenser.calculate(inp_c, outp_c, run_param=run_p_cond, verbose=verbose)
    volumes_c = condenser.calculate_volume()
    
    # condenser.output["state_out"]["working_fluid"]
    
    add_w_o(condenser)
    outputs["config"] = config
    eta_th = np.abs(power_tot) / np.abs(evaporator.output["q_dot"])
    costs = all_costs([pump, evaporator, expander, condenser])
    
    if verbose:      
        print(f"eta_th: {eta_th:.4f}, ",warnings)
   
    # =========== Calculations finished ====================
    if plotting:
    # --------- plot preparation ------------
   
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
                          "label": [pump.name, ""],
                          "col": ["-r", "bv-"]})
        shift, direct = pump.plot(plot_info)
       
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [evaporator.name, ""],
                          "col": [":r", "rv-"]})
        shift, direct = evaporator.plot(plot_info)
       
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [expander.name, ""],
                          "col": ["-b", "bv-"]})
        shift, direct = expander.plot(plot_info)
       
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [condenser_sur.name, ""],
                          "col": [":b", "bv-"]})
        shift, direct = condenser_sur.plot(plot_info)
        
       
        plot_info.update({"x-shift": shift,
                          "direction": direct,
                          "label": [condenser.name, ""],
                          "col": [":r", "rv-"]})
        condenser.plot(plot_info)
        
    results = {"eta_th" : eta_th, 
                          "output" : outputs, 
                           "warnings": warnings, 
                           "figure": fig, 
                           "axes": ax,
                           'costs': costs}
    return results
 
def all_costs(components_all):
    cost_total = 0
    cost_dict ={}

    for proc in components_all:
        cost = proc.estimate_costs()
        cost_total += cost
        cost_dict[proc.name] = cost
        if 'Storage_costs' in proc.output.keys():
            for key, val in proc.output['Storage_costs'].items():
                cost_dict[proc.name+"-storage-" + key] = val
                cost_total +=val
                
        
        print(f'{proc.name} --Exergy destr.rate: {proc.output["exergy_destruction_rate"]:.2e} W, costs: {proc.cost:.2e}')
        if 'Storage_costs' in proc.output.keys():
            print(f"\tStorage costs: {proc.output['Storage_costs']}")
    return {"total_costs":cost_total, "cost_distribution":cost_dict}


if __name__ == "__main__":
    dir_name_m = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-orc-data.yaml"
    conf_m = {"cold_storage": {"temp_low": 254.},
              "working_fluid": {"p_high": 6.2e5,
                               'fractions': [0.75,
                                             0.05,
                                             0.15,
                                             0.05]}}
    result_act = orc(dir_name_m, 3, 1000, config=conf_m,
                                         plotting =True)
    print(result_act["warnings"], result_act["eta_th"])
    