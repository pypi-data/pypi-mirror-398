# -*- coding: utf-8 -*-
"""
heat_exchanger_thermo_vs von ChatGPT überarbeitet
Created on Tue Jul 16 21:30:53 2024

@author: atakan
"""

import copy
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import carbatpy as cb

class StaticHeatExchanger:
    """
    Class for static counter-flow heat exchanger.

   This class models a static counter-flow heat exchanger with no time dependence and no use of UA values (heat transfer coefficients * areas).
   Instead, it tries to meet a minimum approach temperature by varying the mass flow rates and possibly the working fluid pressure in the future.
   Both the first law and the second law of thermodynamics are checked.

   Parameters
   ----------
   fluids : list of fprop.Fluid
       The definition of the two fluids as they enter the heat exchanger, typically at room temperature.
   h_dot_min : float
       The enthalpy flow rate (W) that needs to be transferred.
   h_out_w : float
       The exit enthalpy of the working fluid.
   h_limit_s : float or nan, optional
       If there is a limit in enthalpy for the secondary fluid, it can be given here. The default is nan.
   points : int, optional
       The number of points (array) at which the minimum approach temperature will be checked and properties returned. The default is 30.
   d_temp_separation_min : float, optional
       Minimum approach temperature (pinch point) between the two fluids. The default is 0.5.
   calc_type : str, optional
       The type of calculation to perform; only one type is implemented so far. The default is "const".
   name : str, optional
       Name of the heat exchanger. The default is "evaporator".

   Attributes
   ----------
   all_states : np.ndarray
       Array to store the state properties of the fluids along the heat exchanger.
   dt_mean : float
       Mean temperature difference between the fluids.
   dt_min : float
       Minimum temperature difference between the fluids.
   dt_max : float
       Maximum temperature difference between the fluids.
   warning : int
       Warning code indicating the status of the calculation.
   warning_message : str
       Message describing any warnings that occurred during the calculation.

   Notes
   -----
   The minimum approach temperature is crucial for the design and operation of heat exchangers as it impacts both efficiency and feasibility.
   Future improvements will include varying the working fluid pressure to achieve the desired temperature approach.

   Examples
   --------
   >>> hex = StaticHeatExchanger([fluid1, fluid2], 1000, 200)
   >>> hex.pinch_calc(verbose=True)
    """

    def __init__(self, fluids, h_dot_min, h_out_w, **kwargs):
        """
        Initialize the heat exchanger with given parameters.

        Parameters
        ----------
        fluids : list of 2 fprop.Fluid
            Two fluids entering the heat exchanger, typically at room temperature.
        h_dot_min : float
            Enthalpy flow rate (W) to be transferred.
        h_out_w : float
            Exit enthalpy of the working fluid.
        kwargs : dict, optional
            Optional parameters for the heat exchanger configuration:
                - h_limit_s : float or nan, default np.nan
                - points : int, default 50
                - d_temp_separation_min : float, default 0.5
                - calc_type : str, default "const"
                - name : str, default "evaporator"
                - plot_info : dict, default {}
        """
        self.fluids = fluids
        state_in_w = fluids[0].properties.state

        self.h_dot_min = h_dot_min
        self.h_out_w = h_out_w

        self.h_limit_s = kwargs.get('h_limit_s', np.nan)
        self.points = kwargs.get('points', 50)
        self.d_temp_separation_min = kwargs.get('d_temp_separation_min', 0.5)
        self.calc_type = kwargs.get('calc_type', "const")
        self.name = kwargs.get('name', "evaporator")
        self.plot_info = kwargs.get('plot_info', {})

        self.m_dot_s = 0
        self.q_dot = h_dot_min
        self.m_dot_w = np.abs(h_dot_min / (h_out_w - state_in_w[2]))
        self.h_out_s = float(copy.copy(self.h_limit_s))
        self.heating = 1 if h_out_w < state_in_w[2] else -1

        self.all_states = np.zeros((self.points, len(cb.fprop._THERMO_STRING.split(";"))))
        self.h_in_out = np.zeros((2, 4))
        self.dt_mean = None
        self.dt_min = None
        self.dt_max = None
        self.warning = 0
        self.warning_message = "All o.k."

    @property
    def plot_info(self):
        return self._plot_info

    @plot_info.setter
    def plot_info(self, value):
        if not isinstance(value, dict):
            raise ValueError("plot_info must be a dictionary")
        self._plot_info = value

    def pinch_calc(self, verbose=False):
        """
        Calculate the enthalpy and temperature changes in the heat exchanger.
        Parameters
        ----------
        verbose : bool, optional
            If True, print several variables. Default is False.
        Returns
        -------
        m_dot_s : float
            Secondary fluid mass flow rate (kg/s).
        d_tempall : numpy.ndarray
            Temperature differences along the counter-flow heat exchanger.
        w_array : numpy.ndarray
            Properties of the working fluid along the heat exchanger.
        s_array : numpy.ndarray
            Properties of the secondary fluid along the heat exchanger.
        """
        self.warning = 0
        self.warning_message = "All o.k."
        w_in, s_in = copy.copy(self.fluids[0]), copy.copy(self.fluids[1])
        w_out, s_out = copy.copy(self.fluids[0]), copy.copy(self.fluids[1])
    
        self.h_in_out[1, 0] = s_in.properties.enthalpy
        self.h_in_out[0, 0] = w_in.properties.enthalpy
        self.h_in_out[0, 1] = self.h_out_w
    
        state_out_s = s_out.set_state([self.h_out_s, s_in.properties.pressure], "HP")
        self.h_in_out[1, 1] = state_out_s[2]
        h_delta_s = np.abs(state_out_s[2] - s_in.properties.enthalpy)
        self.m_dot_s = self.q_dot / h_delta_s
    
        s_array = self._calculate_state_array(s_out, self.h_in_out[1, :2], self.points)
        w_array = self._calculate_state_array(w_out, self.h_in_out[0, 1::-1], self.points)
    
        d_tempall = w_array[:, 0] - s_array[:, 0]
        self.dt_mean, self.dt_min, self.dt_max = d_tempall.mean(), np.abs(d_tempall).min(), np.abs(d_tempall).max()
    
        # Debugging-Ausgabe für Temperaturdifferenzen
        print(f"d_tempall: {d_tempall}")
        print(f"Mean T-distance: {self.dt_mean}, Min T-distance: {self.dt_min}, Max T-distance: {self.dt_max}")
    
        self._check_temperature_consistency(d_tempall)
    
        if self.plot_info:
            self._plot_heat_exchanger(w_array, s_array)
    
        if verbose:
            self._print_verbose(d_tempall)
    
        return self.m_dot_s, d_tempall * self.heating, w_array, s_array

    def pinch_root(self, h_out_s, secondary, verbose=False):
        """
        Find the minimum mean temperature difference in the heat exchanger.

        Parameters
        ----------
        h_out_s : float
            The output enthalpy, default for the secondary fluid.
        secondary : bool
            Whether to vary the secondary fluid output (True) or the working fluid (False).

        Returns
        -------
        float
            The mean temperature difference.
        """
        value = h_out_s if isinstance(h_out_s, float) else h_out_s[0]
        self.h_out_s = value if secondary else self.h_out_w
        self.h_out_w = value if not secondary else self.h_out_s

        mdot_s, d_temps, wf_states, sf_states = self.pinch_calc()

        return abs(self.dt_mean) if self.warning < 100 else 500.0

    def find_pinch(self, secondary=True):
        """
        Vary the secondary fluid enthalpy until the minimum approach temperature is reached.
        Parameters
        ----------
        secondary : bool, optional
            Whether to vary the secondary fluid (True) or the working fluid (False). Default is True.
        Returns
        -------
        float
            The optimized enthalpy of the secondary fluid.
        """
        x0 = copy.copy(self.h_out_s if secondary else self.h_out_w)
        tolerance = 1e-3
    
        try:
            result = minimize(self.pinch_root, x0, args=(secondary,), method='Nelder-Mead', tol=tolerance)
    
            if result.success or result.status == 2:
                if result.status == 2:
                    self.warning = 2
                    self.warning_message = "Minimization problem: " + result.message
                self.h_out_s = result.x[0] if secondary else self.h_out_w
                self.h_out_w = result.x[0] if not secondary else self.h_out_s
                print(f"Optimized enthalpy: {result.x[0]}")  # Debugging-Ausgabe
                return result.x[0]
    
        except Exception as e:
            self._handle_exception(e)
            return 10000
    
        self.warning = 1
        return self.warning


    def pinch_plot(self, plot_fname="", plotting=True):
        """
        Calculate and plot the minimum approach temperature of the heat exchanger.

        Parameters
        ----------
        plot_fname : str, optional
            Filename to save the plot. Default is "".
        plotting : bool, optional
            Whether to plot the results. Default is True.

        Returns
        -------
        m_dot_s : float
            Mass flow rate of the secondary fluid in kg/s.
        d_tempall : np.ndarray
            Temperature differences between the two fluids along the heat exchanger.
        w_array : np.ndarray
            States of the working fluid along the heat exchanger.
        s_array : np.ndarray
            States of the secondary fluid along the heat exchanger.
        """
        m_dot_s, d_tempall, w_array, s_array = self.pinch_calc()

        if plotting:
            self._plot_results(w_array, s_array, plot_fname)

        return m_dot_s, d_tempall, w_array, s_array

    def _calculate_state_array(self, fluid, h_range, points):
        h_array = np.linspace(h_range[0], h_range[1], points)
        values = np.zeros((points, 2))
        values[:, 0] = h_array
        values[:, 1] = fluid.properties.pressure
        return fluid.set_state_v(values, "HP")

    def _check_temperature_consistency(self, d_tempall):
        if np.abs(self.dt_min) - self.d_temp_separation_min < 1e-3:
            self.warning = 900
            self.warning_message = "Below minimum approach temperature!"

        if np.any(d_tempall > 0) and np.any(d_tempall < 0):
            self.warning = 999
            self.dt_mean = 1e6
            self.warning_message = "Temperatures crossing or wrong side!"

    def _plot_heat_exchanger(self, w_array, s_array):
        plot_info = self.plot_info
        print("Plot info:", plot_info)  # Debugging-Ausgabe
        if plot_info["what"][0] == 2:
            data_w = (w_array[:, plot_info["what"][0]] - w_array[:, plot_info["what"][0]].min()) * self.m_dot_w + plot_info["x-shift"][0]
            data_s = (s_array[:, plot_info["what"][0]] - s_array[:, plot_info["what"][0]].min()) * self.m_dot_s + plot_info["x-shift"][1]
            plot_info["ax"].plot(data_w, w_array[:, plot_info["what"][1]], plot_info["col"][0], label=plot_info["label"][0])
            plot_info["ax"].plot(data_s, s_array[:, plot_info["what"][1]], plot_info["col"][1], label=plot_info["label"][1])
        else:
            print(f"H-Ex: plotting only implemented for T-H_dot [2,0]. You requested {plot_info['what']}")

    def _print_verbose(self, d_tempall):
        print(f"Min T-distance {self.dt_min}, Mean T-distance {self.dt_mean}")
        if self.heating > 0:
            print("cond", d_tempall[0], d_tempall[-1], d_tempall.min(), d_tempall.max())
        else:
            print("evap", d_tempall[0], d_tempall[-1], d_tempall.max(), d_tempall.min())

    def _handle_exception(self, e):
        print("find pinch:", type(e))
        print(e.args)
        print(e)
        print("root-exception", self.heating)

    def _plot_results(self, w_array, s_array, plot_fname):
        h_w_plot_array = (w_array[:, 2] - w_array[:, 2].min()) * self.m_dot_w
        fig, ax_one = plt.subplots(1, 1)
        ax_one.plot((s_array[:, 2] - s_array[:, 2].min()) * self.m_dot_s, s_array[:, 0], "v")
        ax_one.plot(h_w_plot_array, w_array[:, 0], "o")
        ax_one.set_xlabel("specific enthalpy flow per mass of secondary fluid / (J / kg)")
        ax_one.set_ylabel("temperature / (K)")
        ax_one.set_title("heat exchanger, simple")
        if plot_fname:
            fig.savefig(plot_fname)



if __name__ == "__main__":
    # two test cases condenser and evaporator:

    FLUID = "Propane * Pentane"  # working fluid
    FLS = "Methanol"  # "Water"  # secondary fluid
    comp = [.50, 0.5]
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])
    D_TEMP_MIN = 6.0

    # Condenser, working fluid fixes all, secondary output enthalpy can be varied:
    SEC_TEMP_IN = 300.0
    SEC_TEMP_OUT_MAX = 370.0
    SEC_PRES_IN = 5e5
    H_DOT = 1e3
    state_sec_out = secFluid.set_state([SEC_TEMP_OUT_MAX, SEC_PRES_IN], "TP")

    state_sec_in = secFluid.set_state(
        [SEC_TEMP_IN, SEC_PRES_IN], "TP")  # this is the entering state

    # working fluid

    TEMP_SAT_VAP = SEC_TEMP_OUT_MAX + D_TEMP_MIN
    state_in = myFluid.set_state(
        [TEMP_SAT_VAP, 1.], "TQ")  # find minimum pressure

    WF_TEMP_IN = TEMP_SAT_VAP + D_TEMP_MIN
    WF_TEMP_OUT = SEC_TEMP_IN + D_TEMP_MIN
    state_out = myFluid.set_state([WF_TEMP_OUT, state_in[1]], "TP")

    state_in = myFluid.set_state([myFluid.properties.pressure,
                                  WF_TEMP_IN],
                                 "PT")

    hex0 = StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
                               h_limit_s=state_sec_out[2],
                               d_temp_separation_min=D_TEMP_MIN)
   
    factor0 = hex0.find_pinch()
    if hex0.warning > 0:
        print(hex0.warning_message)
        
    # now plotting can directly be done in pinch_calc 2024-05-24
    fig_act, ax_act = plt.subplots(1)
    PLOT_INFO ={"fig":fig_act, "ax":ax_act, "what":[2,0],"col":["r:","ko"],
    "label":["work,c","sec,c"], "x-shift":[0,0]}
    hex0.plot_info=PLOT_INFO
    hex0.pinch_calc()
    ax_act.legend()
    #-----------------------------------------------
    #       Previous way
    # ms0, d_tempall0, w0, s0 = hex0.pinch_plot("hex-plot.png")
    

    #  Evaporator: ----------------------------

    SEC_TEMP_IN = 300.0
    SEC_TEMP_OUT = 285
    SEC_PRES_IN = 15e5
    H_DOT = 1e3
    extra = 2
    # D_TEMP_SUPER = 5.
    D_TEMP_MIN = 6.0
    state_sec_out = secFluid.set_state([SEC_TEMP_OUT, SEC_PRES_IN], "TP")
    # this mus be the last set_state before the hex is constructed:
    state_sec_in = secFluid.set_state([SEC_TEMP_IN, SEC_PRES_IN], "TP")

    # WF_TEMP_IN = SEC_TEMP_OUT  # - D_TEMP_MIN
    state_out = myFluid.set_state([SEC_TEMP_IN-D_TEMP_MIN - extra, 1.0], "TQ")
    state_in = myFluid.set_state(
        [SEC_TEMP_OUT-D_TEMP_MIN - extra, state_out[1]], "TP")

    # print("state in", state_in)

    hex1 = StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
                               h_limit_s=state_sec_out[2],
                               d_temp_separation_min=D_TEMP_MIN)
    # ms1, d_tempall1, w1, s1 = hex1.pinch_calc()
    

    factor_out = hex1.find_pinch()
    if hex1.warning > 2:
        print("Second heat exchanger:", hex1.warning_message)
    else:

        # plotting in the same figure
        PLOT_INFO ={"fig":fig_act, "ax":ax_act, "what":[2,0],"col":["k:","bo"],
        "label":["work,e","sec,e"], "x-shift":[0,0]}
        hex1.plot_info=PLOT_INFO
        hex1.pinch_calc()
        ax_act.legend()
