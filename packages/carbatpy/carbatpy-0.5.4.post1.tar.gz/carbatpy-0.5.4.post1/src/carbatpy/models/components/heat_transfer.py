# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 10:57:15 2024
wrapper to call ht-database and pressure loss (fluids.friction)

@author: welp
"""

import ht as ht
import carbatpy as cb
import fluids.friction as frict
import numpy as np
from fluids.two_phase import two_phase_dP



def alpha_1P(fluid, fluidstate, mdot, l, d_big, d_small=0):
    """
    heat transfer coefficient in 1phase flow from

    VDI-Wärmeatlas, Kap.G1, 11.Aufl., Springer Vieweg, 2013
    ISBN:  978-3-642-19980-6 / 978-3-642-19981-3
    
    calculates pressure loss with Darcy equiation and Colebrook quation for 
    Darcy friction factor
    

    Parameters
    ----------
    fluid : TYPE
        DESCRIPTION.
    fluidstate : TYPE
        DESCRIPTION. of fluid at given point
    mdot : TYPE
        DESCRIPTION. mass flow rate [kg/s]
    l : TYPE
        DESCRIPTION. length of tube (only used for flow field as reference 
                                     length) [m]
    d_big : TYPE
        DESCRIPTION. diameter [m]
    d_small : TYPE, optional
        DESCRIPTION. The default is 0. inner diameter if annulus [m]

    Returns
    -------
    alpha_i : TYPE
        DESCRIPTION. heat transfer coefficient [W/(m^2*K)]
    dp : TYPE
        DESCRIPTION. differential pressure loss [Pa/m]

    """

    Vdot = mdot * fluidstate.sp_volume  # V = m * v
    u = Vdot / (((d_big/2)**2 - (d_small/2)**2) * np.pi)  # [m/s]  u = Vdot / (pi * r^2)

    dh = d_big - d_small  # if inner tube, d_small zero

    Re = u * dh / (fluidstate.viscosity * fluidstate.sp_volume)  # B1-(10)   u * d / (eta * v)
    
    if Re > 10000:
        ep = 0.045*1e-3
        f_s = frict.Colebrook(Re, ep/dh)
        Xi = (1.8 * np.log10(Re) - 1.5)**-2  # G1-(27)

        Nu = ((Xi/8) * Re * fluidstate.prandtl)/(1 + 12.7 * (Xi/8)**0.5
                                 * (fluidstate.prandtl**(2/3) - 1))\
            * (1+(dh/l)**(2/3))  # G1-(26)

    elif Re > 2300:
        ep = 0.045*1e-3
        f_s = frict.Colebrook(Re, ep/dh)
        gamma = (Re - 2300)/(1e4 - 2300)  # G1-(30)

        Nu_wmq2 = 1.615 * (2300 * fluidstate.prandtl * dh/l)**(1/3)  # G1-(32)
        Nu_wmq3 = (2/(1+22 * fluidstate.prandtl))**(1/6) * (2300 * dh/l)**0.5  # G1-(33)
        Nu_wL = (49.371 + (Nu_wmq2-0.7)**3 + Nu_wmq3**3)**(1/3)  # G1-(31)

        Nu_wT = ((0.0308/8) * 1e4 * fluidstate.prandtl) / \
                (1 + 12.7 * (0.0308/8)**0.5 * (fluidstate.prandtl**(2/3) - 1))  # G1-(37)

        Nu = (1-gamma)*Nu_wL + gamma * Nu_wT  # G1-(29)

    else:
        Nu = 3.66  # G1-(1)
        f_s = 64/Re

    alpha_i = Nu * fluidstate.thermal_conductivity / dh  # [W/m²K] B1-(9)

    dp = f_s / fluidstate.sp_volume * 0.5 * (1/dh) * u**2   # Darcy equation Pa/m
    if np.iscomplexobj(alpha_i):
        raise ValueError(f"error in alpha_i: complex value detected")
    return float(alpha_i), dp

def alpha_km(fluid, fluidstate, mdot, method, l, d_big, U_i=0):
    """
    heat transfer coefficient and pressure drop for working fluid, changes
    automatically to 1phase if necessary.

    Parameters
    ----------
    fluid : TYPE
        DESCRIPTION.
    fluidstate : TYPE
        DESCRIPTION.
    mdot : TYPE
        DESCRIPTION. mass flow rate [kg/s]
    method : TYPE
        DESCRIPTION. Nusselt correlation as in ht database or constant
    l : TYPE
        DESCRIPTION. length of tube (only used for flow field as reference 
                                     length) [m]
    d_big : TYPE
        DESCRIPTION. diameter [m]
        
    U_i : TYPE, optional
        DESCRIPTION. The default is 0. please set, if constant U shall be used

    Returns
    -------
    alpha_KM : TYPE
        DESCRIPTION. heat transfer coefficient [W/(m^2*K)]
    dp_wf : TYPE
        DESCRIPTION. differential pressure loss [Pa/m]

    """  
    
    if 0 < fluidstate.quality < 1:
        # for 2phase
        fluidstate_vap = fluid.set_state([fluidstate.pressure, 1], "PQ", cb.fprop._TRANS_STRING, output="FluidState")
        
        fluidstate_liq = fluid.set_state([fluidstate.pressure, 0], "PQ", cb.fprop._TRANS_STRING, output="FluidState")  # TO DO verify if this saturated state
          # is how it is meant in publication
        
        dp_wf = two_phase_dP(mdot, fluidstate.quality, float(1/fluidstate_liq.sp_volume), d_big, 1,
                                 float(1/fluidstate_vap.sp_volume), float(fluidstate_liq.viscosity),
                                 float(fluidstate_vap.viscosity))
    # =============================================================================
    #         if method == "Chen_Bennett":
    # 
    #             alpha_KM = ht.boiling_flow.Chen_Bennett(
    #                 m, x, D, rhol, rhog, mul, mug, kl, Cpl, Hvap, sigma, dPsat, Te)
    # 
    #         elif method == "Chen_Edelstein":
    # 
    #             alpha_KM = ht.boiling_flow.Chen_Edelstein(
    #                 m, x, D, rhol, rhog, mul, mug, kl, Cpl, Hvap, sigma, dPsat, Te)
    # =============================================================================
            
        if method == "Cavallini_Smith_Zecchin":
            # heat transfer coefficient for condensation of a fluid inside a tube
            alpha_KM = ht.condensation.Cavallini_Smith_Zecchin(mdot, 
                                                               fluidstate.quality, 
                                                               d_big, 
                                                               1/fluidstate_liq.sp_volume, 
                                                               1/fluidstate_vap.sp_volume, 
                                                               fluidstate_liq.viscosity,
                                                               fluidstate_vap.viscosity,
                                                               fluidstate_liq.thermal_conductivity,
                                                               fluidstate_liq.cp,
                                                               )
        elif method == "Chen_Bennett":
            # heat transfer coefficient for film boiling of saturated fluid in any orientation of flow
            sigma = fluid.set_state([fluidstate.pressure, 0], "PQ", "STN")
            alpha_KM = ht.boiling_flow.Chen_Bennett(mdot,
                                                    fluidstate.quality,
                                                    d_big,
                                                    1/fluidstate_liq.sp_volume,
                                                    1/fluidstate_vap.sp_volume,
                                                    fluidstate_liq.viscosity,
                                                    fluidstate_vap.viscosity,
                                                    fluidstate_liq.thermal_conductivity,
                                                    fluidstate_liq.cp,
                                                    fluidstate_vap.enthalpy - fluidstate_liq.enthalpy,
                                                    sigma,
                                                    0,
                                                    0)      # Te and dPsat set to 0
            
        
        elif method == "constant":
            if U_i == 0:
                raise ValueError("U_i needs to be assigned if constant heat\
                                 transfer coefficient is used!")
            alpha_KM = U_i
                
        else:
            raise ValueError(f"method {method} for heat transfer not implemented")

    else:
        # if refrigerant in 1phasestate, mdot, l, d_big, d_small=0
        fluidstate = fluid.set_state([fluidstate.temperature, fluidstate.pressure], 
                                     "TP", cb.fprop._TRANS_STRING, output="FluidState")
        alpha_KM, dp_wf = alpha_1P(fluid, fluidstate, mdot, l, d_big)
    if np.iscomplexobj(alpha_KM):
        raise ValueError("error in alpha_wf: complex value detected")
    return float(alpha_KM) , dp_wf

if __name__ == "__main__":
    FLUID1 = "Propane * Pentane"
    comp1 = [.5, .5]
    fluid1= cb.fprop.init_fluid(FLUID1, comp1)
    st1_in = fluid1.set_state([350., 0.5], "TQ", output="FluidState")
    
    FLUID2 = "water"
    comp2 = [1]
    fluid2 = cb.fprop.init_fluid(FLUID2, comp2)
    st2_in =  fluid2.set_state([300., 1e5], "TP", cb.fprop._TRANS_STRING, output="FluidState")
    
    U_i = 250
    A = 8
    mdot_1, mdot_2 = 0.2, 0.4
    
    alpha1 = alpha_1P(fluid2, st2_in, mdot_2, 10, 20e-3, 15e-3)
    alpha2 = alpha_km(fluid1, st1_in, mdot_1, "Cavallini_Smith_Zecchin", 10, 15e-3)
    alpha3 = alpha_km(fluid1, st1_in, mdot_1, "Chen_Bennett", 10, 15e-3)
    alpha4 = alpha_km(fluid1, st1_in, mdot_1, "constant", 10, 15e-3, U_i = 100)


