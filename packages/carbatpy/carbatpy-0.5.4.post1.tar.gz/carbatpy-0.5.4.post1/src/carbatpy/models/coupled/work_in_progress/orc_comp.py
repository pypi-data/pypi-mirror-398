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
    new_config = kwargs.get("config", None)  # for optimizations
    verbose = kwargs.get("verbose", False)
    
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
    
    
    # ----- pump --------------
    # prescribed power, working_fluid mass flow rate is calculated here
    run_p_comp = {"m_dot": 1.}
    run_p_evap = {"q_dot": q_dot_high}
    q_dot_l = - q_dot_high*(1 - 1/cop)
    run_p_cond = {"q_dot": q_dot_l}
    
    pump = cb.comp.FlowMachine("pump", config)
    p_high = config['working_fluid']['p_high']
    pump.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param={"m_dot": 1.})  # ,  m_dot=10e-3)
    # for the output only p_high is used!  m_dot for the working fluid is calculated later for the evaporator.
    
    evaporator = cb.comp.StaticHeatExchanger("evaporator", config)
    #evaporator.inputs["parameters"]['q_dot']=q_dot_high
    inp1, outp_x = evaporator.set_in_out(
        {'working_fluid': pump.output['state_out']["working_fluid"]})
    evaporator.calculate( inp1, run_param=run_p_evap, verbose=verbose)
    add_w_o(evaporator)
    
    
    m_dot_w = evaporator.output["m_dot"]['working_fluid']
    start = cb.comp.Start("start", config, m_dot=m_dot_w)
    run_p_comp = {"m_dot": m_dot_w}
    pump.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param=run_p_comp, m_dot =m_dot_w)
    
    add_w_o(start)
    add_w_o(pump)
    
    # ----- expander ----------------
    expander = cb.comp.FlowMachine("expander", config)
    
    inp1 = evaporator.output['state_out']
    expander.calculate(inp1,
                         {'working_fluid': [600, p_low, 5e5]},m_dot =m_dot_w,
                         verbose=verbose)
    
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
    
    # condenser.output["state_out"]["working_fluid"]
    
    add_w_o(condenser)
    outputs["config"] = config
    eta_th = np.abs(power_tot) / np.abs(evaporator.output["q_dot"])
    
    print(f"eta_th: {eta_th:.4f}")
   
    # =========== Calculations finished ====================
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
    shift4 = condenser.plot(plot_info)
    return eta_th, outputs, warnings, fig, ax
 
 

if __name__ == "__main__":
    dir_name_m = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-orc-data.yaml"
    conf_m = {"working_fluid": {"p_high": 6.3e5,
                               'fractions': [0.75,
                                             0.05,
                                             0.15,
                                             0.05]}}
    eta_m, ou_m, wa_m, fig_m, ax_m = orc(dir_name_m, 3, 1000, config=conf_m)
    print(wa_m)
    