# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 21:25:43 2024

@author: atakan
"""

import copy
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import carbatpy as cb

class StaticHeatExchanger:
    """
    Static counter-flow heat exchanger class.
    """

    def __init__(self, fluids, h_dot_min, h_out_w, h_limit_s=np.nan, points=50, 
                 d_temp_separation_min=0.5, calc_type="const", name="evaporator"):
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
        h_limit_s : float or nan, optional
            Limit in enthalpy for the secondary fluid. Default is nan.
        points : int, optional
            Number of points for checking minimum approach temperature. Default is 50.
        d_temp_separation_min : float, optional
            Minimum approach temperature between the two fluids. Default is 0.5.
        calc_type : str, optional
            Calculation type. Default is "const".
        name : str, optional
            Name of the heat exchanger. Default is "evaporator".
        """
        self.fluids = fluids
        state_in_w = fluids[0].properties.state
        self.m_dot_s = 0
        self.h_limit_s = h_limit_s
        self.q_dot = h_dot_min
        self.m_dot_w = np.abs(h_dot_min / (h_out_w - state_in_w[2]))
        self.h_out_w = h_out_w
        self.h_out_s = float(copy.copy(h_limit_s))
        self.points = points
        self.d_temp_separation_min = d_temp_separation_min
        self.heating = 1 if h_out_w < state_in_w[2] else -1
        self.calc_type = calc_type
        self.name = name
        self.all_states = np.zeros((points, len(cb.fprop._THERMO_STRING.split(";"))))
        self.h_in_out = np.zeros((2, 4))
        self.dt_mean = None
        self.dt_min = None
        self.dt_max = None
        self.warning = 0
        self.warning_message = "All o.k."

    def pinch_calc(self, verbose=False, plot_info={}):
        """
        Calculate the enthalpy and temperature changes in the heat exchanger.

        Parameters
        ----------
        verbose : bool, optional
            If True, print several variables. Default is False.
        plot_info : dict, optional
            Dictionary with plotting information. Default is empty.

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

        self._check_temperature_consistency(d_tempall)

        if plot_info:
            self._plot_heat_exchanger(plot_info, w_array, s_array)

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

    def _plot_heat_exchanger(self, plot_info, w_array, s_array):
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
