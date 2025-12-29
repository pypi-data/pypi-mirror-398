# -*- coding: utf-8 -*-
"""
Created on Sun May 21 10:52:09 2023

@author: atakan
"""

import copy
import numpy as np
import matplotlib.pyplot as plt


import carbatpy as cb
#from carbatpy import _RESULTS_DIR
_RESULTS_ = cb.CB_DEFAULTS['General']['RES_DIR']


class OrganicRankineCycle:
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
        given. Also, isentropic efficiencies. The COP_charging is important
        to reach a steady state. At the moment you will have to look it up from
        the heat pump calculation. It is used to divide the energy transfered to
        the envoronment and to the low temperature storage.
        Example for::

        fixed_points = {"eta_s": _ETA_S_,  # expander
                        "eta_s_p": _ETA_S_P_,  # pump
                        "p_low": p_low,
                        "p_high": p_high,
                        "T_hh": _STORAGE_T_IN_,
                        "h_h_out_sec": state_sec_out[2],
                        "h_h_out_w": state_out_evap[2],
                        "h_l_out_cold": state_cold_out[2],
                        "h_l_out_w": state_out_cond[2],
                        "h_env_in": state_env_in[2],
                        "h_env_out": state_env_out[2],
                        "T_hl": _STORAGE_T_OUT_,
                        "T_lh": _COLD_STORAGE_T_OUT_,
                        "T_ll": _COLD_STORAGE_T_IN_,  # 256.0,
                        "Q_dot_h": _Q_DOT_MIN_,
                        "d_temp_min": _D_T_MIN_,
                        "cop_charging": _COP_CHARGING  # needed to calculate Q_env_discharging
                        }

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
                           "Power-Net": 0.0,
                           "T_hh": self.fixed_points["T_hh"],
                           "T_ll": self.fixed_points["T_ll"],
                           #"exergy_loss_rate": 0,
                           "eta_pc": 0}
        self.warning = []

    def calc_orc(self,  verbose=False):
        """
        calculate a simple organic rankine cycle (ORC)

        working with two sensible storages (or source and sink). At the moment
        the machine model is just for a constant isentropic efficiency.
        The initial states are provided
        by the Fluid-instances. The pressures have to be selected carefully,
        they are not tested at the moment.
        For optimization, the pressure levels of the cycle could be used within
        a second script. Several parameters are fixed
        along a calculation, this is in the dictionary "self.fixed_points".


        Parameters
        ----------
        verbose : Boolean, optional
            should values be printed? The deault is False

        Returns
        -------
        eta_orc : flaot
            thermal efficiency of ORC.


        """

        state_in = copy.copy(self.fluids[0])  # ORC starts before the pump
        w_actual = self.fluids[0]
        h_initial = w_actual.properties.enthalpy
        if verbose:
            print("Start:")
            w_actual.print_state()

        # pump------------------------
        # w_after_pump, work_pump, _power = \
        #     cb.compressor_simple.compressor(self.fixed_points["p_high"],
        #                                     self.fixed_points["eta_s_p"],
        #                                     self.fluids[0]
        #                                     )
        pump = cb.FlowDeviceOld(self.fluids[0], # plot_info not provided yet!
                                   self.fixed_points["p_high"],
                                   1.0,
                                   device_type="machine",
                                   name="pump",
                                   calc_type="const_eta",
                                   calc_parameters={"eta_s": self.fixed_points["eta_s_p"]},
                                   
                                   )
        w_after_pump, work_pump, _power, s_gen_pump, ex_distruct_pump = pump.state_w_p()

        # the total energy available is given, the mass flow rate of the
        # working fluid should be calculated first.
        m_dot_wf = self.fixed_points["Q_dot_h"] / (self.fixed_points["h_h_out_w"]
                                                   - w_actual.properties.enthalpy)
        # absolute value!
        power_pump = work_pump * m_dot_wf
        if verbose:
            print(f"pump-power {power_pump:.2f} W, m_dot: {m_dot_wf:.4f} kg/s")
            w_actual.print_state()
        evaporator = cb.hex_th.StaticHeatExchanger([w_actual, self.fluids[1]],
                                                   self.fixed_points["Q_dot_h"],
                                                   self.fixed_points["h_h_out_w"],
                                                   self.fixed_points["h_h_out_sec"],
                                                   d_temp_separation_min=self.fixed_points["d_temp_min"],
                                                   calc_type="const",
                                                   name="evaporatorORC")
        result_ev = evaporator.find_pinch(False)
        ms_ev, d_tempall_ec, w_ev, s_ev = evaporator.pinch_plot(
            plotting=verbose)
        if evaporator.warning < 100:
            self.evaluation[evaporator.name] = {
                "dT-min": evaporator.dt_min,
                "dT-mean":  evaporator.dt_mean,
                "Q-dot":  evaporator.q_dot,
                "Warning": evaporator.warning}
        else:
            self.warning.append([evaporator.name, evaporator.warning])

        self.all_states.append(w_ev)
        self.all_states.append(s_ev)
        self.m_dots.append(m_dot_wf)
        self.m_dots.append(ms_ev)
        w_after_evaporator = self.fluids[0].set_state(
            [w_ev[0][2], w_ev[0][1]], "HP")

        if verbose:
            print("after evaporator:")
            w_actual.print_state()

        # expander -----------------------
        # w_after_expander, work_expander, _power =\
        #     cb.compressor_simple.compressor(self.fixed_points["p_low"],
        #                                     self.fixed_points["eta_s"],
        #                                     self.fluids[0]
        #                                     )
        # power = work_expander * m_dot_wf  # absolute value!
        expander = cb.FlowDeviceOld(self.fluids[0],
                                   self.fixed_points["p_low"],
                                   m_dot_wf,
                                   device_type="machine",
                                   name="expander",
                                   calc_type="const_eta",
                                   calc_parameters={"eta_s": self.fixed_points["eta_s"]},
                                   #plot_info =plot_info,
                                   )
        w_after_expander, work_expander, power, s_gen_expander, ex_distruct_expander = expander.state_w_p()
        

        if verbose:
            print(f"After expander, power: {power : .2f}")
            w_actual.print_state()

        # condenser 1: environment------------------------
        q_dot_l = self.fixed_points["Q_dot_h"] * \
            (1-1/self.fixed_points["cop_charging"])
        q_dot_env = self.fixed_points["Q_dot_h"] + power_pump + power - q_dot_l
        h_wf_out_env = w_after_expander[2] - q_dot_env/m_dot_wf
        condenser_env = \
            cb.hex_th.StaticHeatExchanger([w_actual,
                                           self.fluids[2]],
                                          q_dot_env,
                                          h_wf_out_env,
                                          self.fixed_points["h_env_out"],
                                          d_temp_separation_min=self.fixed_points["d_temp_min"],
                                          name="condenserORC_env")
        h_env_out = condenser_env.find_pinch()
        m_dot_envf, d_tempall, wf_states, envf_states =\
            condenser_env.pinch_plot(plotting=verbose)
        if condenser_env.warning < 100:
            self.evaluation[condenser_env.name] = {
                "dT-min": condenser_env.dt_min,
                "dT-mean": condenser_env.dt_mean,
                "Q-dot": condenser_env.q_dot,
                "Warning": condenser_env.warning}
        else:
            self.warning.append([condenser_env.name, condenser_env.warning])

        self.all_states.append(wf_states)
        self.all_states.append(envf_states)
        self.m_dots.append(m_dot_wf)
        self.m_dots.append(m_dot_envf)
        w_after_cond_1 = self.fluids[0].set_state(
            [wf_states[0][2], wf_states[0][1]], "HP")
        if verbose:
            print("After first condenser")
            w_actual.print_state()

        # Now the second condenser is needed  BA 2023-11-28
        condenser = \
            cb.hex_th.StaticHeatExchanger([w_actual,
                                           self.fluids[3]],
                                          q_dot_l,
                                          h_initial,
                                          self.fixed_points["h_l_out_cold"],
                                          d_temp_separation_min=self.fixed_points["d_temp_min"],
                                          name="condenserORC")
        # h_cond_out = condenser.find_pinch() # no degree of freedom left!
        m_dot_cold, d_tempall, wf_cond_states, coldf_states =\
            condenser.pinch_plot(plotting=verbose)
        if condenser.warning < 100:
            self.evaluation[condenser.name] = {
                "dT-min": condenser.dt_min,
                "dT-mean":   condenser.dt_mean,
                "Q-dot":  condenser.q_dot,
                "Warning": condenser.warning}
        else:
            self.warning.append([condenser.name, condenser.warning])
        self.all_states.append(wf_cond_states)
        self.all_states.append(coldf_states)
        self.m_dots.append(m_dot_wf)
        self.m_dots.append(m_dot_cold)

        w_after_condenser = self.fluids[0].set_state([wf_cond_states[0, 1],
                                                      wf_cond_states[0, 2]], "PH")
        if verbose:
            print("after condenser", w_after_condenser)
            w_actual.print_state()
            state_in.print_state()
            q_l_alt = m_dot_wf * (w_after_cond_1-w_after_condenser)[2]
            print(f"q_l comparison {q_dot_l:.2f}, {q_l_alt:.2f}")

        eta_orc = np.abs(power + power_pump)/self.fixed_points["Q_dot_h"]
        self.evaluation["Power-Net"] = np.abs(power + power_pump)
        self.evaluation["Power-Pump"] = np.abs(power_pump)
        self.evaluation["eta_pc"] = eta_orc
        return eta_orc

    def hp_plot(self, f_name=_RESULTS_+"\\last_T_H_dot_plot_orc", fig_ax=[]):
        """
        plots the heat pump cycle and stores it to the given file (name)


        Parameters
        ----------
        f_name : string, optional
            where to write the results and the plot.
        fig_ax : list (length 2), optional
            instances with figure and axes to plot into. If Empty a new one will
            be generated. default =[]
        Returns
        -------
        None.

        """
        states = []
        connect_temp = []
        connect_h = []
        position = [0, -1]
        if len(fig_ax) == 0:
            fig, ax = plt.subplots(1, 1)
        else:
            fig, ax = fig_ax
        points = ["-k", "or", "-b", "vg", "-r", "xg"]
        m_dots = self.m_dots
        n_val = [2, 0]  # positions of h and T
        n_points = np.shape(self.all_states)[1]
        n_range = np.shape(m_dots)[0]  # how many streams? 2 x heat exchangers
        data = np.zeros((n_points, 4))
        names = ["ORC-process",  "{$H_{dot} /W", "T / K", "$m_{dot}"]
        all_data = []

        # m_dots[3] = m_dots[3]  # / m_dots[2] * m_dots[0]
        # m_dots[4] = m_dots[2] = m_dots[0]
        h_shift = 0

        # count backwards to shift the env-hex
        for i_process in range(n_range-1, -1, -1):
            h_shift_here = 0
            if i_process in [2, 3]:  # BA This is specific for this cycle
                h_shift_here = h_shift

            cycle_states = self.all_states[i_process]
            cycle_states = cycle_states[cycle_states[:, 2].argsort(), :]
            if i_process == 4:  # BA This is specific for this cycle
                liquid = self.fluids[0].set_state([cycle_states[0, 1], 0.],
                                                  "PQ")
                ax.plot((liquid[2] - cycle_states[0, 2]) * m_dots[i_process],
                        liquid[0], "o")
            cycle_states[:, 2] -= cycle_states[0, 2]

            cycle_states[:, 2] = cycle_states[:, 2] * \
                m_dots[i_process] + h_shift_here
            states.append(cycle_states)

            if i_process == n_range-1:
                h_shift = cycle_states[-1, 2]

            ax.plot(cycle_states[:, 2], cycle_states[:, 0], points[i_process])
            data[:, 0] = float(i_process)
            data[:, -1] = m_dots[i_process]
            data[:, 1:3] = cycle_states[:, n_val]
            all_data.append(copy.copy(data))

            # pump

            # if i_process in ( 0,2,):  # BA This is specific for this cycle
            #     connect_temp.append(cycle_states[position, 0])
            #     connect_h.append(cycle_states[position, 2])
            #     ax.plot(connect_h, connect_temp, "k:")
            # if i_process in ( 0,4,):  # BA This is specific for this cycle
            #     connect_temp.append(cycle_states[position, 0])
            #     connect_h.append(cycle_states[position, 2])
            #     ax.plot(connect_h, connect_temp, "k:")

        # temperatures = np.array(connect_temp).reshape((4))
        # enthalpies = np.array(connect_h).reshape((4))
        ax.set_xlabel("$\\dot H$ / W")
        ax.set_ylabel("$T$ / K")
        ax.plot([all_data[5][0][1], all_data[1][0][1]],
                [all_data[5][0][2], all_data[1][0][2]], "b:")
        ax.plot([all_data[5][-1][1], all_data[3][-1][1]],
                [all_data[5][-1][2], all_data[3][-1][2]], "k:")

        # for i_process in range(2):
        #     ax.plot([enthalpies[0+i_process], enthalpies[2+i_process]],
        #             [temperatures[0+i_process], temperatures[2+i_process]], "r:")
        fig.savefig(f_name+".png")
        np.savetxt(f_name+".csv", np.concatenate(all_data),
                   delimiter=";", header=";".join(names))


if __name__ == "__main__":

    FLUID = "Propane * Butane * Pentane * Hexane"
    comp = [.75, 0.05, 0.15, 0.05]
    # comp = [0.4,	0.3,	0.3, 0.0]  # [0.164,.3330,.50300,0.0]

    FLS = "Water"  # Storage fluid
    FLCOLD = "Methanol"  # Storage fluid for low T
    FLENV = "Water"  #

    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])

    coldFlm = cb.fprop.FluidModel(FLCOLD)
    coldFluid = cb.fprop.Fluid(coldFlm, [1.])

    envFlm = cb.fprop.FluidModel(FLENV)
    envFluid = cb.fprop.Fluid(secFlm, [1.])

    # Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
    # pressures (p in Pa)
    _ETA_S_ = 0.67  # interesting when changed from 0.69 to 0.65, the efficiency
    # decreases, the reason is the low quality along throtteling then
    _ETA_S_P_ = 0.6  # pump
    _STORAGE_T_OUT_ = cb._T_SURROUNDING
    _COLD_STORAGE_T_OUT_ = cb._T_SURROUNDING
    _ENV_T_IN_ = cb._T_SURROUNDING
    _ENV_T_OUT_ = cb._T_SURROUNDING + 5.
    _STORAGE_T_IN_ = 363.  # 395.0
    _COLD_STORAGE_T_IN_ = 260.15
    _STORAGE_P_IN_ = 5e5
    _COLD_STORAGE_P_IN_ = 5e5
    _ENV_P_IN_ = 5e5
    _Q_DOT_MIN_ = 1e3  # and heat_flow rate (W)
    _D_T_SUPER_ = 5  # super heating of working fluid
    _D_T_MIN_ = 3.  # minimum approach temperature (pinch point)
    _COP_CHARGING = 3.144  # needed to calculate Q_env_discharging
    _T_REDUCTION_EVAP = -22  # if the curves cross in the evaporator this parameter may help
    _DT_COND_ = 7.
    # environment for heat transfer
    state_env_out = envFluid.set_state([_ENV_T_OUT_, _ENV_P_IN_], "TP")
    state_env_in = envFluid.set_state([_ENV_T_IN_, _ENV_P_IN_], "TP")

    # high T-storages
    state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
    state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

    #  low T storages:
    state_cold_out = coldFluid.set_state(
        [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
    state_cold_in = coldFluid.set_state(
        [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

    # working fluid

    state_satv_evap = myFluid.set_state(
        [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_+_T_REDUCTION_EVAP, 1.], "TQ")  # find high pressure
    p_high = state_satv_evap[1]

    T_OUT = _STORAGE_T_IN_ - _D_T_MIN_
    # Evaporator input comes from the pump-output

    state_out_evap = myFluid.set_state([p_high,
                                        T_OUT], "PT")
    # low pressure, condenser # BA 2023-11-14 three points needed: low, environment and slightly higher
    T_SATL = _COLD_STORAGE_T_IN_ + _D_T_MIN_ + _DT_COND_
    state_out_cond = myFluid.set_state([T_SATL, 0.], "TQ")  # find low pressure
    p_low = state_out_cond[1]
    # BA changed 2023-12-13 the fixed starting point for the cycle is the  fluid
    # state before the pump now.

    # the other states in the condenser are fixed by the expander outlet and
    # the Q_total : Q_low_stored ratio    eventually p_low must be varied until
    # the balance is fulfilled, since m_dot_w is fixed by the evaporator!

    FIXED_POINTS = {"eta_s": _ETA_S_,  # expander
                    "eta_s_p": _ETA_S_P_,  # pump
                    "p_low": p_low,
                    "p_high": p_high,
                    "T_hh": _STORAGE_T_IN_,
                    "h_h_out_sec": state_sec_out[2],
                    "h_h_out_w": state_out_evap[2],
                    "h_l_out_cold": state_cold_out[2],
                    "h_l_out_w": state_out_cond[2],
                    "h_env_in": state_env_in[2],
                    "h_env_out": state_env_out[2],
                    "T_hl": _STORAGE_T_OUT_,
                    "T_lh": _COLD_STORAGE_T_OUT_,
                    "T_ll": _COLD_STORAGE_T_IN_,  # 256.0,
                    "Q_dot_h": _Q_DOT_MIN_,
                    "d_temp_min": _D_T_MIN_,
                    "cop_charging": _COP_CHARGING  # needed to calculate Q_env_discharging
                    }

    orc0 = OrganicRankineCycle(
        [myFluid, secFluid, envFluid, coldFluid], FIXED_POINTS)
    eta_dis = orc0.calc_orc(True)
    print(f"eta(ORC): {eta_dis:.4f}")
    orc0.hp_plot()
