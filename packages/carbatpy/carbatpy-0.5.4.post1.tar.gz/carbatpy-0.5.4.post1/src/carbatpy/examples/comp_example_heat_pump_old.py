# -*- coding: utf-8 -*-
"""
An example of using the classes in comp to calculate a heat pump.

Created on Mon Aug 12 17:28:32 2024

@author: atakan
"""

import matplotlib.pyplot as plt
import carbatpy as cb


if __name__ == "__main__":
    # --------- plot preparation ------------

    fig, ax = plt.subplots(1)
    plot_info = cb.CB_DEFAULTS["Components"]["Plot"]
    plot_info.update({"ax": ax, "fig": fig})

    pl_inf = plot_info.copy()  # for the starting point (dot)
    pl_inf.update({"label": ["start", ""],
                   "col": ["ok", "bv"],
                   "direction": 1, })
    # ------- input data -----------
    dir_name = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"

    # ================ CALCULATIONS ==============================
    # ------ Start/initial condition ----
    # but the mass flow rate is yet unknown, plotting must be delayed
    start = cb.comp.Start("start", dir_name, m_dot=10e-3)

    # ----- compressor --------------
    # prescribed power, working_fluid mass flow rate is calculated here
    run_p_comp = {"power": 1500.}
    compressor = cb.comp.FlowMachine("compressor", dir_name)
    p_high = compressor.config['working_fluid']['p_high']
    compressor.calculate(start.output["state_out"],
                         {'working_fluid': [600, p_high, 5e5]},
                         run_param=run_p_comp)  # ,  m_dot=10e-3)
    # for the output only p_high is used! Now m_dot is known for the working fluid.
    m_dot_w = compressor.output["m_dot"]
    start = cb.comp.Start("start", dir_name, m_dot=m_dot_w)

    # ----- coondenser --------------
    run_p_cond = {"m_dot":  m_dot_w}

    condenser = cb.comp.StaticHeatExchanger("condenser", dir_name)
    condenser.calculate(run_param=run_p_cond)

    condenser.output["state_out"]["working_fluid"]
    throttle = cb.comp.Throttle("throttle", dir_name)
    throttle.calculate(condenser.output["state_out"]["working_fluid"],
                       compressor.output["state_in"],
                       m_dot=m_dot_w)

    evaporator = cb.comp.StaticHeatExchanger("evaporator", dir_name)
    inp1, outp1 = evaporator.set_in_out(
        {'working_fluid': throttle.output['state_out']["working_fluid"]})
    inp2, outp2 = evaporator.set_in_out(
        start.output['state_in'], False)
    evaporator.calculate(inp1, outp2, run_param=run_p_cond)

    # =========== Calculations finished ====================
    #
    #     Plotting starts
    shift, direct = start.plot(pl_inf)

    plot_info.update({"x-shift": shift,
                      "direction": direct,
                      "label": [compressor.name, ""]})
    shift, direct = compressor.plot(plot_info)

    plot_info.update({"x-shift": shift,
                      "direction": direct,
                      "label": [condenser.name, ""]})
    shift, direct = condenser.plot(plot_info)

    plot_info.update({"x-shift": shift,
                      "direction": direct,
                      "label": [throttle.name, ""]})
    shift, direct = throttle.plot(plot_info)

    plot_info.update({"x-shift": shift,
                      "direction": direct,
                      "label": [evaporator.name, ""]})
    shift4 = evaporator.plot(plot_info)
