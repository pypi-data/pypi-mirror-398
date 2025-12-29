# -*- coding: utf-8 -*-
"""
Created on Sun May 21 08:51:33 2023

@author: atakan
"""


import carbatpy as cb
import numpy as np


def throttle(p_out, fluid, m_dot=1.0, calc_type="const_h", name="throttle",
             plot_info={}):
    """
    throttle output state calculation

    so far only for a constant enthalpy

    Parameters
    ----------
    p_out : float
        output pressure.
    fluid : fprop.Fluid
        entering fluid, including properties, composition, and model.
    m_dot : float, optional
        mass flow rate (in kg/s). Default is 1
    calc_type : string, optional
        how to calculate, so far, only one implemented. The default is
        "const_h".
    name : string, optional
        name of the device. The default is "throttle".
    plot_info : dictionary, optional
        if not empty a Figure, an Axes, a list of What shall be plotted,
        a list with the colour/styles and a list with the labels must be 
        passed. in "what", the two numbers coincide with the fluid THERMO
        order. The x-shift can be used in cycle calculations, to shift the
        curves, by the value (it will be added).
        The names in the dictionary are: "fig", "ax", "what","col",
        "label", "x-shift". Default is empty.

    Returns
    -------
    state_out : array of float
        compressor output state containing [T,p,h,v,s,q].

    """
    state_in = fluid.properties.state
    if calc_type == "const_h":
        state_out = fluid.set_state([fluid.properties.enthalpy, p_out], "HP")
    else:
        raise Exception(
            f"The option{calc_type} is not yet implemented for throttles")
        
    cb.compressor_simple.plot_temp_h_flow(state_in, state_out, m_dot, plot_info)   
    # 
    return state_out


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    M_DOT = 1e-3
    fig0, ax0 = plt.subplots()
    PLOT_INFO ={"fig":fig0, "ax":ax0, "what":[2,0],"col":["r:","k"],
    "label":["throttle","xx"], "x-shift":[0,0]}
    
    FLUID = "Propane * Pentane"
    comp = [.50, 0.5]
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)
    state_in = myFluid.set_state([320., 19e5], "TP")

    P_OUT = 5e5

    state_out_main = throttle(P_OUT, myFluid, plot_info=PLOT_INFO)
    print("Throttle:\nInput:", state_in, "\nOutput:",
          state_out_main, "\nDifference", state_out_main-state_in)
