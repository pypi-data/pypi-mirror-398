# -*- coding: utf-8 -*-
"""
Created on Sun Nov  5 10:01:28 2023

@author: atakan
"""
import numpy as np
import carbatpy as cb

n_pos=[0,2,4]
def s_irr_flow(states, mass_flow_rates, verbose=False, entropy_position=4):
    """
    Irreversible entropy production rate for two fluid flows or an adiabatic
    heat exchanger. It is intended to use for heat pumps, where energy is
    stored at low and at high temperature.

    Parameters
    ----------
    states : numpy-array [n,2,7]
        the states to analyse ordered as entering fluids[:,0,:] and exiting
        fluid [:,1,:] the states are as defined in fluid_props, with the 4th
        value being the specific entropy in J/(kg K)(see below).
    mass_flow_rates : numpy array of length n
        the mass flow rates in SI units (kg/s).
    verbose : Boolean, optional
        should we print? The default is False.
    entropy_position : Integer, optional
        in the states array, where to find thge specific entropy.
        The default is 4.

    Returns
    -------
    float
        entropy production rate in W/K.

    """

    # state in always first
    s_irr = -(states[:, 0, entropy_position] -
              states[:, 1, entropy_position]) * mass_flow_rates
    if verbose:
        print("Sirr:", s_irr, states[:,:,n_pos], mass_flow_rates, s_irr.sum())
    return s_irr.sum()


def exergy_loss_alternative(states, mass_flow_rates,  power_in=0.,
                            temp_surrounding=cb._T_SURROUNDING,
                            verbose=False, entropy_position=4,
                            enthaply_position=2):
    """
    assumption both fluids enter in equilibrium with the surrounding
    if entropy is reduced, T is below the environment T and exergy is positive
    
    but this not correct yet, should be implemented correctly 
    """
    ds = states[:, 0, entropy_position] - states[:, 1, entropy_position]
    dh = states[:, 0, enthaply_position] - states[:, 1, enthaply_position]
    dex = (dh - ds * temp_surrounding) * mass_flow_rates
    if verbose:
        print("Ex-Alt:", dh*mass_flow_rates, ds*mass_flow_rates, mass_flow_rates, dex, power_in)
        print("in:",states[:,0,n_pos])
        print("out:",states[:,1,n_pos])
        print("dex",dex)
    dex_total = power_in + np.sum(dex)
    return dex_total  # must be checked, if more than two streams are analyzed


def exergy_loss_flow(states, mass_flow_rates, power_in=0.,
                     temp_surrounding=cb._T_SURROUNDING,
                     verbose=False, entropy_position=4):
    """
    Calculate the exergy loss rate for two fluid flows or an adiabatic
    heat exchanger. It is intended to use for heat pumps, where energy is
    stored at low and at high temperature. Uses s_irr_flow. All parameters are
    described there, except one. Gouy-Stodola


    Parameters
    ----------
    states : TYPE
        DESCRIPTION.
    mass_flow_rates : TYPE
        DESCRIPTION.
    power_in : TYPE, optional
        DESCRIPTION. The default is 0..
    temp_surrounding : Float, optional
        surrounding temperature in K. The default is cb._T_SURROUNDING.
    verbose : TYPE, optional
        DESCRIPTION. The default is False.
    entropy_position : TYPE, optional
        DESCRIPTION. The default is 4.

    Returns
    -------
    float
        Exergy loss rate in W.

    """

    s_irr = s_irr_flow(states, mass_flow_rates,
                       verbose=verbose, entropy_position=entropy_position
                       )

    return s_irr * temp_surrounding #+ power_in


if __name__ == "__main__":
    FLUID = "Propane * Pentane"
    comp = [.50, 0.5]
    P_OUT = 5e5
    power = 15000.00 
    m_dots = np.array((1.4, 1))  # important different signs
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)
    
    state_in = myFluid.set_state([320., 19e5], "TP")
    state_out = myFluid.set_state([300, 19e5], "TP")
    
    state_in_2 = myFluid.set_state([290., 19e5], "TP")
    h2o = state_in_2[2] + (m_dots[0]*(state_in-state_out)[2] + power)/m_dots[1]
    state_out_2 = myFluid.set_state([h2o, 19e5], "HP")
    print("States\n",state_in[n_pos], state_out[n_pos],
          state_in_2[n_pos], state_out_2[n_pos], h2o, m_dots)

    states = np.array([[state_in, state_out], [state_in_2, state_out_2]])
    print("Irr-Gouy-Stod1\n",s_irr_flow(states, m_dots), exergy_loss_flow(states, m_dots, power_in=power))
    print("Ex_loss2\n", exergy_loss_alternative(states, m_dots, power_in=power))
