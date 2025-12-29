# -*- coding: utf-8 -*-
"""
Created on Sun May 21 10:52:09 2023

@author: atakan
"""

import copy
import numpy as np
import matplotlib.pyplot as plt

import carbatpy as cb

_RESULTS_ = r"C:\Users\atakan\sciebo\results\\"


class HeatPump:
    """
    Heat pump class for simple thermodynamic calculations for energy storage

    Two pairwase storages at two different temperatures are assumed,
    always starting at room temperature (around 300K). Thus, three fluids are
    expected: the working fluid, the storage fluid  or sink at high temperature
    (h) and the source storage fluid at low temperature.
    The minimum and maximum temperatures of all 
    storags are fixed and the heat flow rate to the high-T storage are 
    given. Also, isentropic efficiencies are fixed so far, but they should use
    a function later.
    """

    def __init__(self,  fluids, fixed_points, components=[]):
        """
        Heat pump class for simple thermodynamic calculations for energy storage

        storages at two different temperatures, always starting at room 
        temperature (around 300K). The minimum and maximum temperatures aof all 
        storags are fixed and the heat flow rate to the high-T storage are 
        given. Also, isentropic efficiencies.
        Example for
        fixed_points = {"eta_s": 0.65,
                        "p_low": p_low,
                        "T_hh": _STORAGE_T_OUT_,
                        "T_hl": _STORAGE_T_IN_,
                        "T_lh": _STORAGE_T_IN_,
                        "T_ll": 257.,  # 256.0,
                        "Q_dot_h": 3000.0,
                        "d_temp_min": _D_T_MIN_}

        Parameters
        ----------
        fluids : list of three Fluid
            working fluid, secondary fluid to store at high T, cold fluid
            to store at low T.
        fixed_points : Dictionary
            all the fixed points are summarized here, the isentropic efficiency,
            the lower pressure(evaporator), the high and low temperatures of
            the high temperature storages, the same for the low temperature
            storages(source), the heat to be transfered at high T, the minimum
            approach temperature.
        components : TYPE, optional
            DESCRIPTION. The default is [].

        Returns
        -------
        None.

        """
        self.components = components
        self.fixed_points = fixed_points
        self.fluids = fluids
        self.all_states = []
        self.m_dots = []
        self.evaluation = {"Q_dot_h": self.fixed_points["Q_dot_h"],
                           "Power": 0.0,
                           "p_high": 0.0,
                           "p_low!": self.fixed_points["p_low"],
                           "exergy_loss_rate": 0}

    def calc_p_high(self, p_high, verbose=True):
        """
        calculate a simple compression heat pump 

        working with two sensible storages (or source and sink). At the moment
        the compressor model is just for a constant isentropic efficiency.
        An isenthalpic throttle is used for expnsion. The initial states are provided
        by the Fluid-instances. The pressures have to be selected carefully,
        they are not tested at the moment. The high pressure is an input, and
        can easily be used for optimization. Several parameters are fixed
        along a calculation, this is in the dictionary "self.fixed_points".
        It can turn out that the foreseen evaporator exit temperature of the 
        secondary(cooling) fluid is below the temperature of the isenthalpic 
        temperature of the fluid coming out of the throttle. In this case the 
        secondary exit temperature is increased.

        Parameters
        ----------
        p_high : float
            working fluid pressure (Pa) in the condenser (=const.).
        verbose : Boolean, optional
            should values be printed? The deault is False

        Returns
        -------
        COP : flaot
            coefficient of performace.


        """

        state_in = copy.copy(self.fluids[0])
        w_actual = self.fluids[0]
        if verbose:
            print(
                "Initial:", self.fluids[0].properties.temperature,
                state_in.properties.enthalpy)
        w_after_compressor = \
            cb.compressor_simple.compressor(p_high, self.fixed_points["eta_s"],
                                            self.fluids[0])
        if verbose:
            print("behind compressor",
                  self.fluids[0].properties.temperature, w_after_compressor)

        condenser = \
            cb.hex_th.StaticHeatExchanger([w_actual,
                                           self.fluids[1]],
                                          self.fixed_points["Q_dot_h"],
                                          self.fixed_points["T_hh"],
                                          d_temp_separation_min=self.fixed_points["d_temp_min"],
                                          name="condenser")
        factor = condenser.find_pinch()
        m_dot_wf, d_tempall, wf_states, sf_states =\
            condenser.pinch_plot(factor, plotting=False)
        self.all_states.append(wf_states)
        self.all_states.append(sf_states)
        self.m_dots.append(m_dot_wf)
        self.m_dots.append(condenser.m_dot_s)

        w_after_condenser = self.fluids[0].set_state([wf_states[0, 1],
                                                      wf_states[0, 2]], "PH")
        if verbose:
            print("after condenser")
            w_actual.print_state()

        power = (w_after_compressor[2] -
                 state_in.properties.enthalpy) * m_dot_wf
        heat_flow_evap = self.fixed_points["Q_dot_h"] - power
        if verbose:
            print(
                f"power:{ power} W, heat-Evap. {heat_flow_evap} W\n")
        w_after_throttle = cb.throttle_simple.throttle(self.fixed_points["p_low"],
                                                       self.fluids[0])

        if verbose:
            print("after throttle:")
        w_act = w_actual.set_state(
            [w_after_throttle[1], w_after_throttle[2]], "PH")
        if self.fixed_points["T_ll"] < w_act[0] + self.fixed_points["d_temp_min"]:
            self.fixed_points["T_ll"] = w_act[0] + \
                self.fixed_points["d_temp_min"]
        if verbose:
            w_actual.print_state()

        evaporator = cb.hex_th.StaticHeatExchanger([w_actual, self.fluids[2]],
                                                   heat_flow_evap,
                                                   self.fixed_points["T_ll"],
                                                   d_temp_separation_min=self.fixed_points["d_temp_min"],
                                                   calc_type="const",
                                                   name="evaporator")
        # factor_ev = evaporator.find_pinch()[0]
        # problem, must perhaps be rewritten, because the mass flow in the cycle is fixed:
        mw_ev, d_tempall_ec, w_ev, s_ev = evaporator.pinch_plot(
            factor, plotting=False)

        self.all_states.append(w_ev)
        self.all_states.append(s_ev)
        self.m_dots.append(m_dot_wf)
        self.m_dots.append(evaporator.m_dot_s*m_dot_wf/mw_ev)
        w_after_evap = self.fluids[0].set_state([w_ev[0, 1], w_ev[0, 2]], "PH")
        q_evap = (w_after_evap[2] - w_after_throttle[2]) * m_dot_wf
        if heat_flow_evap - q_evap > 1:
            print(f"heat pump cycle not steady{heat_flow_evap, q_evap}")
        if verbose:
            print(f"  heat after Evaporator:{q_evap},power:{power}")
            w_actual.print_state()
            print("-test-", (sf_states[-1] - sf_states[0])*self.m_dots[1],
                  (s_ev[-1]-s_ev[0])*self.m_dots[-1])
        sec_fluids_states_in_out = np.array([[sf_states[0], sf_states[-1]],
                                            [s_ev[0], s_ev[-1]]])
        
        mass_flow_rates = np.array([self.m_dots[1], self.m_dots[-1]])

        ex_loss_rate = cb.exlo.exergy_loss_flow(sec_fluids_states_in_out,
                                                mass_flow_rates)
        ex_loss_alte = cb.exlo.exergy_loss_alternative(sec_fluids_states_in_out,
                                                       mass_flow_rates,
                                                       power_in=power)
        self.evaluation = {"Q_dot_h": self.fixed_points["Q_dot_h"],
                           "Power": power,
                           "p_high": p_high,
                           "p_low": self.fixed_points["p_low"],
                           "exergy_loss_rate": ex_loss_rate,
                           "exergy_loss_alte": ex_loss_alte}
        return self.fixed_points["Q_dot_h"] / power

    def hp_plot(self, f_name=_RESULTS_+"last_T_H_dot_plot"):
        """
        plots the heat pump cycle and stores it to the given file (name)

        Returns
        -------
        None.

        """
        states = []
        connect_temp = []
        connect_h = []
        position = [0, -1]
        fig, ax = plt.subplots(1, 1)
        points = ["-k", "or", "-b", "vg"]
        m_dots = self.m_dots

        m_dots[3] = m_dots[3] / m_dots[2] * m_dots[0]
        m_dots[2] = m_dots[0]

        for i_process in range(4):

            cycle_states = self.all_states[i_process]
            cycle_states = cycle_states[cycle_states[:, 2].argsort(), :]
            if i_process == 2:
                liquid = self.fluids[0].set_state([cycle_states[0, 1], 0.],
                                                  "PQ")
                ax.plot((liquid[2] - cycle_states[0, 2]) * m_dots[i_process],
                        liquid[0], "o")
            cycle_states[:, 2] -= cycle_states[0, 2]

            cycle_states[:, 2] = cycle_states[:, 2] * m_dots[i_process]
            states.append(cycle_states)

            ax.plot(cycle_states[:, 2], cycle_states[:, 0], points[i_process])
            if i_process == 0 or i_process == 2:
                connect_temp.append(cycle_states[position, 0])
                connect_h.append(cycle_states[position, 2])
        temperatures = np.array(connect_temp).reshape((4))
        enthalpies = np.array(connect_h).reshape((4))
        ax.set_xlabel("$\dot H$ / W")
        ax.set_ylabel("$T$ / K")

        for i_process in range(2):
            ax.plot([enthalpies[0+i_process], enthalpies[2+i_process]],
                    [temperatures[0+i_process], temperatures[2+i_process]], "r:")
        fig.savefig(f_name+".png")


if __name__ == "__main__":

    FLUID = "Propane * Butane * Pentane * Hexane"
    comp = [.75, 0.05, 0.15, 0.05]
    comp = [0.4,	0.3,	0.3, 0.0]  # [0.164,.3330,.50300,0.0]

    FLS = "Water"  #
    FLCOLD = "Methanol"  # "Water"  #

    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])

    coldFlm = cb.fprop.FluidModel(FLCOLD)
    coldFluid = cb.fprop.Fluid(coldFlm, [1.])

    # Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
    # pressures (p in Pa)
    _ETA_S_ = 0.637  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    _STORAGE_T_IN_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_IN_ = _STORAGE_T_IN_
    _STORAGE_T_OUT_ = 363.  # 395.0
    _COLD_STORAGE_T_OUT_ = 260.15-5
    _STORAGE_P_IN_ = 5e5
    _COLD_STORAGE_P_IN_ = 5e5
    _Q_DOT_MIN_ = 1e3  # and heat_flow rate (W)
    _D_T_SUPER_ = 5  # super heating of working fluid
    _D_T_MIN_ = 5.  # minimum approach temperature (pinch point)

    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid
    T_DEW = _STORAGE_T_OUT_ - _D_T_SUPER_
    state_in = myFluid.set_state([T_DEW, 1.], "TQ")  # find minimum pressure
    # changed by hand, to make the _D_T_MIN_ possible
    p_high_act = state_in[1] * .99

    state_in = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_SUPER_-_D_T_MIN_, 1.], "TQ")  # find minimum pressure
    p_low = state_in[1]
    T_IN = _STORAGE_T_IN_  # - _D_T_MIN_
    # state_in = myFluid.set_state([p_low,
    #                               _STORAGE_T_IN_ - _D_T_MIN_], "PT")
    print(f"p-ratio: {p_high_act/p_low: .2f}, p_low: {p_low/1e5: .2} bar")
    state_in = myFluid.set_state([p_low,
                                  T_IN], "PT")

    FIXED_POINTS = {"eta_s": _ETA_S_,
                    "p_low": p_low,
                    "T_hh": _STORAGE_T_OUT_,
                    "T_hl": _STORAGE_T_IN_,
                    "T_lh": _STORAGE_T_IN_,
                    "T_ll": _COLD_STORAGE_T_OUT_,  # 256.0,
                    "Q_dot_h": _Q_DOT_MIN_,
                    "d_temp_min": _D_T_MIN_}

    hp0 = HeatPump([myFluid, secFluid, coldFluid], FIXED_POINTS)
    cop = hp0.calc_p_high(p_high_act, verbose=True)
    hp0.hp_plot()
    out = hp0.evaluation
    print(
        f"COP: {cop},p-ratio: {out['p_high']/out['p_low']:.2f}, p_low {out['p_low']/1e5:.2f} bar")
    print(
        f"COP: {cop},p-ratio: {out['p_high']/out['p_low']}, p_low {out['p_low']/1e5}")
    print(
        f'exergy loss rate: {out["exergy_loss_rate"]}, eff: {1-out["exergy_loss_rate"]/out["Power"]:.4f}')
    print(
        f'power= {out["Power"]:.2f} W, Alternative Ex-Loss:{out["exergy_loss_alte"]:.4f}')
    print(f'eff_alternative: {1-out["exergy_loss_alte"]/out["Power"]:.4f}')
