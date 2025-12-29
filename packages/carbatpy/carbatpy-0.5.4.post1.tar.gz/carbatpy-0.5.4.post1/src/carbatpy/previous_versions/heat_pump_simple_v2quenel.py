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
                        "p_high": p_high,
                        "T_hh": _HIGH_T_STORAGE_HIGH_TEMP,
                        "T_hl": _HIGH_T_STORAGE_LOW_TEMP,
                        "T_lh": _LOW_T_STORAGE_HIGH_TEMP,
                        "T_ll": _LOW_T_STORAGE_LOW_TEMP,
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
                           "T_hh": self.fixed_points["T_hh"],
                           "T_ll": self.fixed_points["T_ll"],
                           "exergy_loss_rate": 0}

    def calculate_hex(self, fluid_numbers, h_dot_min_, h_out_w_, h_limit_s_=np.NAN,
                      points_=50, d_temp_separation_min_=0.5, calc_type_="const",
                      name_="evaporator", verbose_=True):
        """
        Utility function to calculate the T-h_dot curves and secondary fluid

        mass flow rates for a heat exchanger. it returns the state of the
        working fluid at the heat exchanger exit. while

        Parameters
        ----------
        fluid_numbers : list of two integers
            the working fluid index and the secondary fluid index.
        h_dot_min_ : float
            wanted heat flow rate [W].
        h_out_w_ : float
            specific enthalpy of the working fluid at the exit  [J/kg].
        h_limit_s_ : float, optional
            specific enthalpy of the secondary fluid at the exit  [J/kg].
            The default is np.NAN.
        points_ : integer, optional
            number of t-h points along the heat exchanger. The default is 50.
        d_temp_separation_min_ : float, optional
            the minimum approach temperature in K. The default is 0.5.
        calc_type_ : string, optional
            select the calculation type (only one implemented for now). The
            default is "const".
        name_ : string, optional
            name of the heat exchanger. The default is "evaporator".
        verbose_ : Boolean, optional
            additional printing/plotting. The default is False.

        Returns
        -------
        w_after_condenser : list
            actual output state of the working fluid [T,p,h,v,s,q].

        """
        w_actual, s_actual = [self.fluids[fluid_numbers[0]],
                              self.fluids[fluid_numbers[1]]]
        hex_act = \
            cb.hex_th.StaticHeatExchanger([w_actual,
                                           s_actual],
                                          h_dot_min_, h_out_w_, h_limit_s_,
                                          d_temp_separation_min=d_temp_separation_min_,
                                          name=name_)
        h_s_out = hex_act.find_pinch()
        m_dot_s, d_tempall, wf_states, sf_states =\
            hex_act.pinch_plot(plotting=verbose_)

        self.all_states.append(wf_states)
        self.all_states.append(sf_states)
        self.m_dots.append(hex_act.m_dot_w)
        self.m_dots.append(m_dot_s)

        w_after_hex = self.fluids[0].set_state([wf_states[0, 1],
                                                wf_states[0, 2]], "PH")
        fluids_states_in_out = np.array([[wf_states[0], wf_states[-1]],
                                         [sf_states[0], sf_states[-1]]]
                                        )
        fluids_states_in_out_ex = fluids_states_in_out
        if hex_act.heating < 1:
            fluids_states_in_out_ex = np.flip(fluids_states_in_out, axis=1)

        mass_flow_rates = np.array([hex_act.m_dot_w,
                                    hex_act.m_dot_s])

        ex_loss_rate = cb.exlo.exergy_loss_flow(fluids_states_in_out_ex,
                                                mass_flow_rates)
        self.evaluation[name_] = [fluids_states_in_out,
                                  mass_flow_rates,
                                  ex_loss_rate]
        if verbose_:
            print(f"after heat exchanger: {name_}")
            w_actual.print_state()
        return w_after_hex

    def calc_p_high(self, temps_wanted, verbose=False):
        """
        calculate a simple compression heat pump

        working with two sensible storages (or source and sink). At the moment
        the compressor model is just for a constant isentropic efficiency.
        An isenthalpic throttle is used for expnsion. The initial states are provided
        by the Fluid-instances. The pressures have to be selected carefully,
        they are not tested at the moment. The two desired storage temperatures
        are an input, and will be varied to meet the desired minmum approach
        temperatures in the heat exchangers.
        For optimization, the pressure levels of the cycle could be used within
        a second script. Several parameters are fixed
        along a calculation, this is in the dictionary "self.fixed_points".
        It can turn out that the foreseen evaporator exit temperature of the
        secondary(cooling) fluid is below the temperature of the isenthalpic
        temperature of the fluid coming out of the throttle. In this case the
        secondary exit temperature is increased.

        Parameters
        ----------
        temps_wanted : np.array([float,float])
            the two (high and low) temperatures to store at, may be varied
            towards the temperature of the surrounding, if the second law
            of thermodynamics requires this.
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
            print("Start:")
            w_actual.print_state()
        # compressor -----------------------
        w_after_compressor, work_c = \
            cb.compressor_simple.compressor(self.fixed_points["p_high"], self.fixed_points["eta_s"],
                                            self.fluids[0])
        if verbose:
            print("After compressor")
            w_actual.print_state()

        # condenser ------------------------                                       "PT")
        # condenser = \
        #     cb.hex_th.StaticHeatExchanger([w_actual,
        #                                    self.fluids[1]],
        #                                   self.fixed_points["Q_dot_h"],
        #                                   self.fixed_points["h_h_out_w"],
        #                                   self.fixed_points["h_h_out_sec"],
        #                                   d_temp_separation_min=self.fixed_points["d_temp_min"],
        #                                   name="condenser")
        # h_s_out = condenser.find_pinch()
        # m_dot_s, d_tempall, wf_states, sf_states =\
        #     condenser.pinch_plot(plotting=False)
        # m_dot_wf = self.fixed_points["Q_dot_h"] / \
        #     (wf_states[-1, 2] - wf_states[0, 2])
        # self.all_states.append(wf_states)
        # self.all_states.append(sf_states)
        # self.m_dots.append(m_dot_wf)
        # self.m_dots.append(m_dot_s)

        fluid_nos = [0, 1]

        w_after_condenser = self.calculate_hex(fluid_nos,
                                               self.fixed_points["Q_dot_h"],
                                               self.fixed_points["h_h_out_w"],
                                               self.fixed_points["h_h_out_sec"],
                                               d_temp_separation_min_=self.fixed_points["d_temp_min"],
                                               name_="condenser",
                                               verbose_=verbose)

        power = work_c * self.m_dots[fluid_nos[0]]
        heat_flow_evap = self.fixed_points["Q_dot_h"] - power
        if verbose:
            print(
                f"power:{ power} W, heat-Evap. {heat_flow_evap} W\n")

        # throttle--------------------
        w_after_throttle = cb.throttle_simple.throttle(self.fixed_points["p_low"],
                                                       w_actual)

        if verbose:
            print("after throttle:")
            print(w_actual.print_state())
        w_act = w_actual.set_state(
            [w_after_throttle[1], w_after_throttle[2]], "PH")
        if self.fixed_points["T_ll"] < w_act[0] + self.fixed_points["d_temp_min"]:
            self.fixed_points["T_ll"] = w_act[0] + \
                self.fixed_points["d_temp_min"]
        if verbose:
            w_actual.print_state()

        fluid_nos2 = [0, 2]

#         evaporator = cb.hex_th.StaticHeatExchanger([w_actual, self.fluids[2]],
#                                                    heat_flow_evap,
#                                                    self.fixed_points["h_l_out_w"],
#                                                    self.fixed_points["h_l_out_cold"],
#                                                    d_temp_separation_min=self.fixed_points["d_temp_min"],
#                                                    calc_type="const",
#                                                    name="evaporator")
#         factor_ev = evaporator.find_pinch()
#         ms_ev, d_tempall_ec, w_ev, s_ev = evaporator.pinch_plot(
#             plotting=False)

#         self.all_states.append(w_ev)
#         self.all_states.append(s_ev)
#         self.m_dots.append(m_dot_wf)
#         self.m_dots.append(ms_ev)


# #####################################################
#         w_after_evap = self.fluids[0].set_state([w_ev[0, 1], w_ev[0, 2]], "PH")
        w_after_evap = self.calculate_hex(fluid_nos2,
                                          heat_flow_evap,
                                          self.fixed_points["h_l_out_w"],
                                          self.fixed_points["h_l_out_cold"],
                                          d_temp_separation_min_=self.fixed_points["d_temp_min"],
                                          calc_type_="const",
                                          name_="evaporator",
                                          verbose_=verbose
                                          )

        q_evap = (w_after_evap[2] - w_after_throttle[2]
                  ) * self.m_dots[fluid_nos2[0]]
        if heat_flow_evap - q_evap > 1:
            print(f"heat pump cycle not steady{heat_flow_evap, q_evap}")
        if verbose:
            print(f"  heat after Evaporator:{q_evap},power:{power}")
            w_actual.print_state()
        #     print("-test-", (sf_states[-1] - sf_states[0])*self.m_dots[1],
        #           (s_ev[-1]-s_ev[0])*self.m_dots[-1])
        sec_fluids_states_in_out = np.array([self.evaluation["condenser"][0][-1],
                                             self.evaluation["evaporator"][0][-1]])

        mass_flow_rates = np.array([self.evaluation["condenser"][1][-1],
                                    self.evaluation["evaporator"][1][-1]])

        ex_loss_rate = cb.exlo.exergy_loss_flow(sec_fluids_states_in_out,
                                                mass_flow_rates)
        # ex_loss_alte = cb.exlo.exergy_loss_alternative(sec_fluids_states_in_out,
        #                                                mass_flow_rates,
        #                                                power_in=power)
        cop = self.fixed_points["Q_dot_h"] / power
        self.evaluation.update({"Q_dot_h": self.fixed_points["Q_dot_h"],
                                "Power": power,
                                "p_high": self.fixed_points["p_high"],
                                "p_low": self.fixed_points["p_low"],
                                "exergy_loss_rate": ex_loss_rate,
                                # "exergy_loss_alte": ex_loss_alte,
                                "sec_fluid_states_in_out": sec_fluids_states_in_out,
                                "sec_fluid_m_dots": mass_flow_rates,
                                "COP": cop
                                })
        return cop

    def hp_plot(self, f_name=_RESULTS_+"last_T_H_dot_plot_hp"):
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
        n_val = [2, 0]  # positions of h and T
        n_points = np.shape(self.all_states)[1]
        n_range = np.shape(m_dots)[0]  # how many streams? 2 x heat exchangers
        data = np.zeros((n_points, 4))
        names = ["HP-process", "{$H_{dot} /W", "T / K", "$m_{dot}"]
        all_data = []

        m_dots[3] = m_dots[3]  # / m_dots[2] * m_dots[0]
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
            data[:, 0] = float(i_process)
            data[:, -1] = m_dots[i_process]
            data[:, 1:3] = cycle_states[:, n_val]
            all_data.append(copy.copy(data))
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
        np.savetxt(f_name+".csv", np.concatenate(all_data),
                   delimiter=";", header=";".join(names))


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
    _ETA_S_ = 0.67  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    _STORAGE_T_IN_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_IN_ = _STORAGE_T_IN_
    _STORAGE_T_OUT_ = 363.  # 395.0
    _COLD_STORAGE_T_OUT_ = 260.15
    _STORAGE_P_IN_ = 5e5
    _COLD_STORAGE_P_IN_ = 5e5
    _Q_DOT_MIN_ = 1e3  # and heat_flow rate (W)
    _D_T_SUPER_ = 5  # super heating of working fluid
    _D_T_MIN_ = 4.  # minimum approach temperature (pinch point)
    # high T-storages
    state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

    #  low T storages:
    state_cold_out = coldFluid.set_state(
        [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid
    T_DEW = _STORAGE_T_OUT_  # + _D_T_MIN_
    state_in_cond = myFluid.set_state([T_DEW, 1.], "TQ")  # find high pressure
    state_out_cond = myFluid.set_state([_STORAGE_T_IN_ + _D_T_MIN_,
                                        state_in_cond[1]], "TP")
    state_satv_evap = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_, 1.], "TQ")  # find minimum pressure
    p_low = state_satv_evap[1]

    T_IN = _STORAGE_T_IN_ - _D_T_MIN_

    state_out_evap = myFluid.set_state([p_low,
                                        T_IN], "PT")

    FIXED_POINTS = {"eta_s": _ETA_S_,
                    "p_low": state_out_evap[1],
                    "p_high": state_in_cond[1],
                    "T_hh": _STORAGE_T_OUT_,
                    "h_h_out_sec": state_sec_out[2],
                    "h_h_out_w": state_out_cond[2],
                    "h_l_out_cold": state_cold_out[2],
                    "h_l_out_w": state_out_evap[2],
                    "T_hl": _STORAGE_T_IN_,
                    "T_lh": _STORAGE_T_IN_,
                    "T_ll": _COLD_STORAGE_T_OUT_,  # 256.0,
                    "Q_dot_h": _Q_DOT_MIN_,
                    "d_temp_min": _D_T_MIN_}

    print(
        f"p-ratio: {state_in_cond[1]/state_out_evap[1]: .2f}, p_low: {state_out_evap[1]/1e5: .2} bar")
    hp0 = HeatPump([myFluid, secFluid, coldFluid], FIXED_POINTS)
    print(hp0.evaluation)
    cop = hp0.calc_p_high(FIXED_POINTS["p_high"], verbose=True)
    print(hp0.evaluation)
    hp0.hp_plot()
    print(hp0.evaluation, "----------------n")
    out = hp0.evaluation
    print(
        f"COP: {cop},p-ratio: {out['p_high']/out['p_low']:.2f}, p_low {out['p_low']/1e5:.2f} bar")

    print(
        f'exergy loss rate: {out["exergy_loss_rate"]}, eff: {1-out["exergy_loss_rate"]/out["Power"]:.4f}')
