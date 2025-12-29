# -*- coding: utf-8 -*-
"""
Created on Sun May 21 08:51:33 2023

@author: atakan
"""


import copy
import carbatpy as cb
# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import root
import matplotlib.pyplot as plt


class StaticHeatExchanger:
    """
    Class for static counter-flow heat exchanger

    means: no time dependence and no heat transfer coefficients * areas
    are used (UA)! Instead a minimum approach temperature is tried to be met.
    At the moment, this is mainly done by varying one of the mass flow rates.
    But this is sometimes not enough and a variation of the working fluid
    pressure will soon be included.
    Only the first law and second law will be checked (the latter must be
    improved).

    """

    def __init__(self, fluids, h_dot_min, temp_out_s,
                 points=50, d_temp_separation_min=0.5, calc_type="const",
                 name="evaporator"):
        """
        class to calculate (static/steady state) heat-exchangers

        includes pinch-point analysis and plotting,
        only implemented for simple thermodynamic calculations
        (no convection coefficients and heat exchanger areas regarded yet)

        Parameters
        ----------
        fluids : list of 2 fprop.Fluid
            The definition of the two fluids, as they enter the heat exchanger.
        h_dot_min : float
            enthalpy flow rate (W) which has to be transfered.
        temp_out_s : float
            exit temperature of the secondary fluid.
        points : integer, optional
            for how many points (array) shall the minimum approach temperature
            be checked and properties be returned (for plotting etc.)
            The default is 30.
        d_temp_separation_min : float, optional
            Minimium approach temperature (pinch point) between the two fluids.
            The default is 0.5.
        calc_type : string, optional
            which calculation type shall be performed; only one implemented so
            far. The default is "const".
        name : string, optional
            name of the heat exchanger. The default is "evaporator".

        Returns
        -------
        None.

        """
        self.fluids = fluids
        self.q_dot = h_dot_min
        self.m_dot_s = 0
        self.temp_out_s = temp_out_s
        self.points = points
        self. d_temp_separation_min = d_temp_separation_min
        self.heating = False
        if temp_out_s > fluids[1].properties.temperature:
            self.heating = True  # condenser
        self.calc_type = calc_type
        self.name = name
        self.all_states = np.zeros((points, len(cb.fprop._THERMO_STRING)))
        self.h_in_out = np.zeros((2, 4))
        self.warning = 0


    def pinch_calc(self, m_dot_w_factor=1, verbose=False):
        """
        Calculate the changes in enthalpy and temperature in the heat exchanger

        counter-flow hex assumed! Both flows are isobaric.
        Is used to check, whether the second law is violated. The factor can
        be used to vary the mass flow rate of the working fluid, until no
        violation is found (done in root finding).

        Parameters
        ----------
        m_dot_w_factor : float, optional
            factor to divide the working fluid mass flow rate, as derived from
            the enrgy balance, in order to avoid a crossing of temperature
            curves. The default is 1.

        Raises
        ------
        Exception
            if temperatures are not consistent.

        Returns
        -------
        m_dot_w : float
            working fluid mass flow rate (kg/s.
        d_tempall : numpy-array
            The temperature differences along the counter-flow heat exchanger.
        w_array : array
            properties of the working fluid along the heat exchanger
            (T,p,h, etc. see fluid class).
        s_array : array
            properties of the secondary fluid along the heat exchanger
            (T,p,h, etc. see fluid class).

        """
        w_in = self.fluids[0]
        s_in = self.fluids[1]

        w_out = copy.copy(self.fluids[0])
        s_out = copy.copy(self.fluids[1])

        self. h_in_out[1, 0] = h_in_s = s_in.properties.enthalpy
        h_in_w = w_in.properties.enthalpy

        # fixed output temperature, secondary fluid
        s_out.set_state([self.temp_out_s, s_in.properties.pressure], "TP")
        if self.heating:
            condenser = 1
        else:
            condenser = -1

        self. h_in_out[1, 1] = h_dot_s = (
            s_out.properties.enthalpy - s_in.properties.enthalpy) * condenser
        # fixed heat flow,  determines mass flow rate
        self.m_dot_s = self.q_dot / h_dot_s

        outw = w_out.set_state([s_in.properties.temperature +
                                self.d_temp_separation_min * condenser,
                                w_in.properties.pressure], "TP")
        hw_max = outw[2]
        h_dot_w_max = np.abs(w_in.properties.enthalpy - hw_max)
        mw_max = self.q_dot / h_dot_w_max
        # bei reiner propan WP geht etwas schief, BA
        if verbose:
            print("mw_max", mw_max, self.q_dot)
        m_dot_w = mw_max * m_dot_w_factor  # scaling for minimum approach T
        h_dot_w = h_dot_w_max / m_dot_w_factor
        h_out_w = h_in_w - condenser * h_dot_w
        if np.isscalar(h_dot_w):
            pass
        else:
            h_dot_w = h_dot_w[0]
            h_out_w = h_out_w[0]

        self. h_in_out[0, 0] = h_out_w

        self. h_in_out[0, 1] = h_dot_w

        # check pinch, first secondary fluid
        h_array = np.linspace(h_in_s, h_in_s + h_dot_s *
                              condenser, self.points)
        values = np.zeros((self.points, 2))
        values[:, 0] = h_array
        values[:, 1] = s_out.properties.pressure

        s_array = s_out.set_state_v(values, given="HP")

        # now working fluid:
        h_array = np.linspace(self.h_in_out[0, 0],
                              self.h_in_out[0, 0] +
                              self.h_in_out[0, 1] * condenser,
                              self.points)

        values = np.zeros((self.points, 2))
        values[:, 0] = h_array.T
        values[:, 1] = w_out.properties.pressure

        w_array = w_out.set_state_v(values, "HP")
        d_tempall = w_array[:, 0]-s_array[:, 0]
        if verbose:
            if condenser == -1:
                print("evap", d_tempall[0], d_tempall[-1],
                      d_tempall.max(), d_tempall.min())
            else:
                print("cond", d_tempall[0], d_tempall[-1],
                      d_tempall.min(), d_tempall.max())
        return m_dot_w, d_tempall, w_array, s_array

    def pinch_root(self, factor, verbose=False):
        """
        function for root-finding of the minimum approach temperature

        a factor to divide the working fluid mass flow rate is varied. input
        for root

        Parameters
        ----------
        factor : float
            as said above.

        Returns
        -------
        float
            root tries to reach a value of 0.

        """
        mw, d_temps, w, s = self.pinch_calc(factor)
        mind_temp = d_temps.min()
        maxd_temp = d_temps.max()
        if mind_temp/maxd_temp <= 0:
            return 1e6
        # todo: check that all signs of d_temps are equal, if not:return values !=0
        if self.heating:
            if verbose:
                print("H", mind_temp - self.d_temp_separation_min,
                      d_temps.min(), self.d_temp_separation_min, mw)
            return mind_temp - self.d_temp_separation_min
        else:
            if verbose:
                print("HC", maxd_temp + self.d_temp_separation_min,
                      d_temps.max(), self.d_temp_separation_min, mw)
            return maxd_temp + self.d_temp_separation_min

    def find_pinch(self):
        """
        Function tries to vary one mass flow rate until a minimum approach
        temperature is reached. If this is not successful, the working fluid
        pressure is varied within 20 percent. This is then also the new pressure
        within the heat exchanger. If this is also not succesful,
        self.warning is set to 1. This should be checked.

        Returns
        -------
        float
            the factor to multiply the mass flow rate with, to reach the 
            minimum approach temperature. Igf not succesful the initial factor
            is returned.

        """
        verbose = False
        w_initial = copy.copy(self.fluids[0])
        p0 = w_initial.properties.pressure
        enthalpy = w_initial.properties.enthalpy

        P_VARIATION = 0.2
        N_VARIATION = 21
        if self.heating:
            start = 1.05
            p_var = np.linspace(p0, p0*(1+P_VARIATION), N_VARIATION)
        else:
            start = .95
            p_var = np.linspace(p0, p0*(1-P_VARIATION), N_VARIATION)
        try:
            for pressure in p_var:
                self.fluids[0].set_state([pressure, enthalpy], "PH")
                result = root(self.pinch_root, start)
                if verbose:
                    print(
                        f"pressure:{pressure}, result {result}, heating {self.heating}")

                if result.success:
                    return result.x[0]

        # except:
        except Exception as inst:
            print(type(inst))    # the exception type
            print(inst.args)     # arguments stored in .args
            print(inst)          # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses

            result = np.array([1e4])
            print("root-exception", self.heating)
            return result
        print("root-finding problem! (in heat_exchanger_thermo_v2.find_pinch)",
              result)
        print(f"Heating: {self.heating}")
        self.warning = 1
        return self.factor

    def pinch_plot(self, factor, plot_fname="", plotting=True):
        print(f"------pinch-plot running -----plot:{plotting}")
        m_dot_w, d_tempall, w_array, s_array = self.pinch_calc(factor)

        h_w_plot_array = (
            w_array[:, 2] - self.h_in_out[0, 0]) * m_dot_w / self.m_dot_s
        if plotting:
            fig, ax = plt.subplots(1, 1)
            ax.plot(s_array[:, 2] - self.h_in_out[1, 0], s_array[:, 0], "v")
            ax.plot(h_w_plot_array, w_array[:, 0], "o")
            ax.set_xlabel(
                "specific enthalpy flow per mass of secondary fluid / (J / kg)")
            ax.set_ylabel("temperature / (K)")
            ax.set_title("heat exchanger, simple")
        if plot_fname != "":
            fig.savefig(plot_fname)

        return m_dot_w, d_tempall, w_array, s_array


if __name__ == "__main__":
    # two test cases condenser and evaporator:
    FLUID = "Propane * Pentane"  # working fluid
    FLS = "Methanol"  # "Water"  # secondary fluid
    comp = [.50, 0.5]
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])

    # Condenser, secondary fluid fixes all:
    sT_in = 300.0
    sT_out = 370.0
    sp_in = 5e5
    h_dot_min = 1e3

    state_sec_in = secFluid.set_state([sT_in, sp_in], "TP")
    # working fluid
    d_temp_super = 5.
    T_dew = sT_out
    state_in = myFluid.set_state([T_dew, 1.], "TQ")  # find minimum pressure

    T_in = T_dew + d_temp_super
    state_in = myFluid.set_state([myFluid.properties.pressure,
                                  myFluid.properties.temperature + d_temp_super],
                                 "PT")
    d_temp_min = 3.0

    hex0 = StaticHeatExchanger([myFluid, secFluid], h_dot_min, sT_out,
                               d_temp_separation_min=d_temp_min)
    mw, d_tempall, w, s = hex0.pinch_calc(1.1)
    factor0 = hex0.find_pinch()
    mw0, d_tempall0, w0, s0 = hex0.pinch_plot(factor0)
    print(f"w0 {w0[0]}")

    # Evaporator: ----------------------------

    sT_in = 300.0
    sT_out = 276
    sp_in = 5e5
    h_dot_min = 1e3

    state_sec_in = secFluid.set_state([sT_in, sp_in], "TP")
    d_temp_min = 2.0
    T_in = sT_out  # - d_temp_min
    state_in = myFluid.set_state([T_in, .1], "TQ")
    print("state in", state_in)

    hex0 = StaticHeatExchanger([myFluid, secFluid], h_dot_min, sT_out,
                               d_temp_separation_min=d_temp_min)
    mw, d_tempall, w, s = hex0.pinch_calc(1)
    factor = hex0.find_pinch()
    mw, d_tempall, w, s = hex0.pinch_plot(factor)
    print(f"w {w[0]}")

    p_out = 5e5

    # state_out = throttle(p_out, myFluid)
    # print("Throttle:\nInput:", state_in,"\nOutput:",
    # state_out,"\nDifference", state_out-state_in)
