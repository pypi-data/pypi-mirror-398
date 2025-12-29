# -*- coding: utf-8 -*-
"""
Version for new FlowDevices

Changed on 2024-07-18

@author: atakan
"""

import copy
import json
import yaml
import numpy as np
import matplotlib.pyplot as plt
import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable


_RESULTS_ = cb.CB_DEFAULTS["General"]["RES_DIR"]

DEFAULT_DIR = cb.CB_DEFAULTS["General"]["CB_DATA"]
DEFAULT_FILE = DEFAULT_DIR+"\\hp-input-dictvariables"

class HeatPump(Serializable):
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
    default_path = DEFAULT_DIR
    default_filename = DEFAULT_FILE+"-hp.json"
    default_storage_filename = DEFAULT_FILE+"-hp-last.json"
    def __init__(self,   fixed_points, components=None):
        """
        Heat pump class for simple thermodynamic calculations for energy storage

        storages at two different temperatures, always starting at room
        temperature (around 300K). The minimum and maximum temperatures aof all
        storags are fixed and the heat flow rate to the high-T storage are
        given. Also, isentropic efficiencies.
        Example for the fixed points::

        fixed_points = {"ETA_S_C": _ETA_S_,
                        "p_low": state_out_evap[1],
                        "p_high": state_in_cond[1],
                        "T_OUT_STORAGE_HOT": _STORAGE_T_OUT_,
                        "h_h_out_sec": state_sec_out[2],
                        "h_h_out_w": state_out_cond[2],
                        "h_l_out_cold": state_cold_out[2],
                        "h_l_out_w": state_out_evap[2],
                        "T_hl": _STORAGE_T_IN_,
                        "T_lh": _STORAGE_T_IN_,
                        "T_OUT_STORAGE_COLD": _COLD_STORAGE_T_OUT_,  # 256.0,
                        "Q_DOT_MIN": _Q_DOT_MIN_,
                        'D_T_MIN': _D_T_MIN_
                        'fluids_all': fluids # see below}

        Parameters
        ----------
        fluids : list of three lists with three values
            working fluid, secondary fluid to store at high T, cold fluid
            to store at low T [what, species-string, composition-list], what is one of
            "STORAGE_COLD", "STORAGE_HOT" or "WORKING".
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
        if components:
            self.components = components
        else:
            self.components ={}
        self.fixed_points = fixed_points
        self.fluids_all = copy.copy(fixed_points["fluids_all"])
        self.fluids = []
        for fll, ii in self.fluids_all.items():
            self.fluids.append(set_fl_state([fll,*ii], fixed_points)[0])


        self.all_states = []
        self.m_dots = []
        self.warning = []
        self.evaluation = {"Q_DOT_MIN": self.fixed_points["Q_DOT_MIN"],
                           "Power": 0.0,
                           "T_OUT_STORAGE_HOT": self.fixed_points["T_OUT_STORAGE_HOT"],
                           "T_OUT_STORAGE_COLD": self.fixed_points["T_OUT_STORAGE_COLD"],
                           "exergy_loss_rate": 0
                           }
    # @property
    # def all(self):
    #     # Erstelle ein Dictionary aller Attribute außer self.all
    #     return {key: value for key, value in self.__dict__.items()
    #             if key not in( 'all', "fluids", "all_states")}

    # def _is_serializable(self, value):
    #     try:
    #         json.dumps(value)
    #         return True
    #     except (TypeError, OverflowError):
    #         return False

    # def _to_serializable(self, value):
    #     if isinstance(value, np.ndarray):
    #         return value.tolist()
    #     elif hasattr(value, 'to_dict'):
    #         return value.to_dict()
    #     elif isinstance(value, dict):
    #         return {k: self._to_serializable(v) for k, v in value.items() if self._is_serializable(v)}
    #     elif isinstance(value, list):
    #         return [self._to_serializable(item) for item in value if self._is_serializable(item)]
    #     elif isinstance(value, (int, float, str, bool, np.float64)):
    #         return value
    #     else:
    #         return str(value)

    # def to_dict(self):
    #     result = {}
    #     for key, value in self.__dict__.items():
    #         if key not in (all,'fluids, "all_states') and self._is_serializable(value):
    #             result[key] = self._to_serializable(value)
    #     return result

    # @classmethod
    # def from_dict(cls, data):
    #     instance = cls.__new__(cls)
    #     for key, value in data.items():
    #         if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
    #             setattr(instance, key, np.array(value))
    #         elif isinstance(value, dict) and 'value' in value:
    #             setattr(instance, key, AnotherClass.from_dict(value))
    #         else:
    #             setattr(instance, key, value)
    #     return instance

    # def save_to_file(self, file_path):
    #     try:
    #         data = self.to_dict()
    #         if file_path.endswith('.json'):
    #             with open(file_path, 'w') as file:
    #                 json.dump(data, file, indent=4)
    #         elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
    #             with open(file_path, 'w') as file:
    #                 yaml.dump(data, file, default_flow_style=False)
    #         else:
    #             raise ValueError("Unsupported file format. Use .json or .yaml/.yml")
    #     except Exception as e:
    #         print(f"Error saving to file: {e}")

    # @classmethod
    # def load_from_file(cls, file_path):
    #     try:
    #         if file_path.endswith('.json'):
    #             with open(file_path, 'r') as file:
    #                 data = json.load(file)
    #         elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
    #             with open(file_path, 'r') as file:
    #                 data = yaml.load(file, Loader=yaml.SafeLoader)
    #         else:
    #             raise ValueError("Unsupported file format. Use .json or .yaml/.yml")

    #         return cls.from_dict(data)
    #     except Exception as e:
    #         print(f"Error loading from file: {e}")
    #         return None


    def calculate_hex(self, fluid_numbers, h_dot_min_, h_out_w_, h_limit_s_=np.nan,
                      points_=50, d_temp_separation_min_=0.5, calc_type_="const",
                      pinch="", name_="evaporator",
                      plot_info={}, verbose_=False):
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
        pinch : string, optional
            shall a minimization of the mean temperture difference be performed?
            ""-> no, "secondary"-> output state of secondary fluid will be
            varied, "working"-> the ouput state of the working fluid will be
            varied. Default is ""
        name_ : string, optional
            name of the heat exchanger. The default is "evaporator".
        plot_info : dictionary, optional
            if not empty a Figure, an Axes, a list of What shall be plotted,
            a list with the colour/styles and a list with the labels must be
            passed. in "what", the two numbers coincide with the fluid THERMO
            order. The x-shift can be used in cycle calculations, to shift the
            curves, by the value (it will be added).
            The names in the dictionary are: "fig", "ax", "what","col",
            "label", "x-shift". Default is empty.
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
        match pinch:  # noqa
            case "":
                h_s_out = hex_act.pinch_calc(plot_info)
            case "secondary":
                h_s_out = hex_act.find_pinch()

            case "working":
                h_s_out = hex_act.find_pinch(False)
            case _:
                print("calculate_hex: This option is not available")

        if hex_act.warning > 0:
            print("Heat-Exchanger problem: ",
                  hex_act.warning, hex_act.warning_message)
            self.warning.append(
                [hex_act.name, hex_act.warning, hex_act.warning_message])
        m_dot_s, d_tempall, wf_states, sf_states =\
            hex_act.pinch_plot(plotting=verbose_)
        d_temp_mean = hex_act.dt_mean
        d_temp_min = hex_act.dt_min

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
        self.evaluation[name_] = {
            "states-in-out": fluids_states_in_out,
            "mass-flow-rates": mass_flow_rates,
            "exergy-loss-rate":  ex_loss_rate,
            "dT-min":  d_temp_min,
            "dT-mean": d_temp_mean}
        self.components[name_]=hex_act.all
        if verbose_:
            print(f"after heat exchanger: {name_}")
            w_actual.print_state()
        return w_after_hex

    def calc_heat_pump(self, plot_info={}, variations=["", ""], verbose=False):
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
        secondary exit temperature is increased!

        Parameters
        ----------
        temps_wanted : np.array([float,float])
            the two (high and low) temperatures to store at, may be varied
            towards the temperature of the surrounding, if the second law
            of thermodynamics requires this. UNUSED at the moment!
        verbose : Boolean, optional
            should values be printed? The deault is False

        Returns
        -------
        COP : flaot
            coefficient of performace.


        """

        state_in = copy.copy(self.fluids[0])
        w_actual = self.fluids[0]
        warn_act =None
        if verbose:
            print("Start:")
            w_actual.print_state()
        # compressor -----------------------
        # w_after_compressor, work_c, _power = \
        #     cb.compressor_simple.compressor(self.fixed_points["p_high"],
        #                                     self.fixed_points["ETA_S_C"],
        #                                     self.fluids[0])
        compressor = cb.FlowDeviceOld(self.fluids[0],
                                   self.fixed_points["p_high"],
                                   1.0,
                                   device_type="machine",
                                   name="compressor",
                                   calc_type="const_eta",
                                   calc_parameters={"eta_s": self.fixed_points["ETA_S_C"]},
                                   plot_info=plot_info
                                   )
        w_after_compressor, work_c, _power, s_gen_c, ex_distruct_compressor = compressor.state_w_p()
        self.components[compressor.name] = compressor.all
        if verbose:
            print("After compressor")
            w_actual.print_state()

        # condenser -------------------------
        fluid_nos = [0, 1]

        w_after_condenser = self.calculate_hex(fluid_nos,
                                               self.fixed_points["Q_DOT_MIN"],
                                               self.fixed_points["h_h_out_w"],
                                               self.fixed_points["h_h_out_sec"],
                                               d_temp_separation_min_=self.fixed_points['D_T_MIN'],
                                               name_="condenser",
                                               calc_type_=variations[0],
                                               plot_info=plot_info,
                                               verbose_=verbose)

        _power = work_c * self.m_dots[fluid_nos[0]]
        heat_flow_evap = self.fixed_points["Q_DOT_MIN"] - _power
        if verbose:
            print(
                f"power:{ _power} W, heat-Evap. {heat_flow_evap} W\n")

        # throttle--------------------
        # w_after_throttle = cb.throttle_simple.throttle(self.fixed_points["p_low"],
        #                                                w_actual)
        throttle = cb.FlowDeviceOld(w_actual, self.fixed_points["p_low"],
                                 self.m_dots[fluid_nos[0]],
                                 device_type="throttle",
                                 name="throttle-A",
                                 calc_type="const_h",
                                 calc_parameters={},
                                 plot_info=plot_info)
        w_after_throttle = throttle.output["state_out"]
        self.components[throttle.name] = throttle.all

        if verbose:
            print("after throttle:")
            print(w_actual.print_state())
        w_act = w_actual.set_state(
            [w_after_throttle[1], w_after_throttle[2]], "PH")
        if isinstance(self.fixed_points['T_OUT_STORAGE_COLD'], np.float64):
            warn_act = f"""T_OUT_STORAGE_COLD probably changed  to {self.fixed_points["T_OUT_STORAGE_COLD"]:.2f} K!"""
            self.warning.append(warn_act)
            
        if self.fixed_points["T_OUT_STORAGE_COLD"] < w_act[0] + self.fixed_points['D_T_MIN']:
            self.fixed_points["T_OUT_STORAGE_COLD"] = w_act[0] + \
                self.fixed_points['D_T_MIN']
            warn_act = f"""T_OUT_STORAGE_COLD changed  to {self.fixed_points["T_OUT_STORAGE_COLD"]:.2f} K!"""
            self.warning.append(warn_act)

        # evaporator -------------------
        fluid_nos2 = [0, 2]
        w_after_evap = self.calculate_hex(fluid_nos2,
                                          heat_flow_evap,
                                          self.fixed_points["h_l_out_w"],
                                          self.fixed_points["h_l_out_cold"],
                                          d_temp_separation_min_=self.fixed_points['D_T_MIN'],
                                          name_="evaporator",
                                          calc_type_=variations[0],
                                          plot_info=plot_info,
                                          verbose_=verbose
                                          )

        q_evap = (w_after_evap[2] - w_after_throttle[2]
                  ) * self.m_dots[fluid_nos2[0]]
        if heat_flow_evap - q_evap > 1:
            print(f"heat pump cycle not steady{heat_flow_evap, q_evap}")
        if verbose:
            print(f"  heat flow rate evaporator:{q_evap},power:{_power}")
            w_actual.print_state()

        sec_fluids_states_in_out = np.array([self.evaluation["condenser"]["states-in-out"][-1],
                                             self.evaluation["evaporator"]["states-in-out"][-1]])

        mass_flow_rates = np.array([self.evaluation["condenser"]["mass-flow-rates"][-1],
                                    self.evaluation["evaporator"]["mass-flow-rates"][-1]])

        ex_loss_rate_total = cb.exlo.exergy_loss_flow(sec_fluids_states_in_out,
                                                mass_flow_rates) #BA 2025-01-23 add m_dot[0] *ex_distr, throttle nd compressor
        
        
        def invert_array_order(np_array):
            inv_array = copy.copy(np_array)
            inv_array[[0, 1]] = inv_array[[1, 0]]
            return inv_array
        
        #exergy losses for each component:
        condenser_fluids_states_in_out = np.array([self.evaluation["condenser"]["states-in-out"][-1],
                                             invert_array_order(self.evaluation["condenser"]["states-in-out"][0])])
        condenser_mass_flow_rates = np.array([self.evaluation["condenser"]["mass-flow-rates"][-1],
                                    self.evaluation["condenser"]["mass-flow-rates"][0]])
        condenser_ex_loss_rate = cb.exlo.exergy_loss_flow(condenser_fluids_states_in_out,
                                                condenser_mass_flow_rates)
        
        
        evaporator_fluids_states_in_out = np.array([invert_array_order(self.evaluation["evaporator"]["states-in-out"][0]),
                                             self.evaluation["evaporator"]["states-in-out"][-1]])
        evaporator_mass_flow_rates = np.array([self.evaluation["evaporator"]["mass-flow-rates"][0],
                                    self.evaluation["evaporator"]["mass-flow-rates"][-1]])
        evaporator_ex_loss_rate = cb.exlo.exergy_loss_flow(evaporator_fluids_states_in_out,
                                                evaporator_mass_flow_rates)
        exergy_destr_devices={"compressor": compressor.output['exergy_destruction_spcific'] * self.m_dots[0],
                              "condenser": condenser_ex_loss_rate,
                              "throttle": throttle.output['exergy_destruction_spcific'] * self.m_dots[0],
                              "evaporator":evaporator_ex_loss_rate,
                              }
        
        
        cop = self.fixed_points["Q_DOT_MIN"] / _power
        self.evaluation.update({"Q_DOT_MIN": self.fixed_points["Q_DOT_MIN"],
                                "Power": _power,
                                "p_high": self.fixed_points["p_high"],
                                "p_low": self.fixed_points["p_low"],
                                "exergy_loss_rate_total": ex_loss_rate_total,
                                 "exergy_destruct_device": exergy_destr_devices,
                                "sec_fluid_states_in_out": sec_fluids_states_in_out,
                                "sec_fluid_m_dots": mass_flow_rates,
                                "COP": cop,
                                "Message": warn_act,
                                })
        return cop

    def hp_plot(self, f_name=_RESULTS_+"\\last_T_H_dot_plot_hp"):
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
        ax.set_xlabel('$ \\dot H$ / W')
        ax.set_ylabel("$T$ / K")

        for i_process in range(2):
            ax.plot([enthalpies[0+i_process], enthalpies[2+i_process]],
                    [temperatures[0+i_process], temperatures[2+i_process]], "r:")
        fig.savefig(f_name+".png")
        np.savetxt(f_name+".csv", np.concatenate(all_data),
                   delimiter=";", header=";".join(names))
        np.save(f_name+"_evaluation_dict.npy", self.evaluation)
        return [fig, ax]

def set_fl_state(fluid_values, fixed_points,
                  **kwargs):

    fluid_act = cb.init_fluid(*fluid_values[1:])
    fl_type = fluid_values[0]
    if "STORAGE" in fl_type:
        p_in, t_in, t_out = _extract_storage_values(fixed_points, fl_type)
        state_out = fluid_act.set_state([t_out, p_in], "TP")
        state_in = fluid_act.set_state([t_in, p_in], "TP")

        if "HOT" in fl_type:
            fixed_points['h_h_out_sec'] = state_out[2]
            return fluid_act, fixed_points
        elif "COLD" in fl_type:
            fixed_points['h_l_out_cold'] = state_out[2]

            return fluid_act, fixed_points

    w_p_select =fixed_points["P_WORKING"]
    if w_p_select["setting"]== "auto":
        state_in_cond = fluid_act.set_state(
            [fixed_points['T_OUT_STORAGE_HOT'], 1.], "TQ")  # find high pressure
        p_high = state_in_cond[1]

        state_out_cond = fluid_act.set_state([fixed_points['T_IN_STORAGE_HOT'] +
                                            fixed_points['D_T_MIN'],
                                            p_high], "TP")
        # evaporator now
        T_IN = fixed_points['T_IN_STORAGE_COLD'] - fixed_points['D_T_MIN']
        state_satv_evap = fluid_act.set_state(
            [T_IN -
             fixed_points['D_T_SUPER'], 1.], "TQ")  # find minimum pressure
        p_low = state_satv_evap[1]

        state_out_evap = fluid_act.set_state([p_low,
                                            T_IN], "PT")
    else:
        p_high =  w_p_select["p_high"]
        p_low =  w_p_select["p_low"]
        state_in_cond = fluid_act.set_state(
            [fixed_points['T_OUT_STORAGE_HOT'],p_high], "TP")  # find high pressure


        state_out_cond = fluid_act.set_state([fixed_points['T_IN_STORAGE_HOT'] +
                                            fixed_points['D_T_MIN'],
                                            p_high], "TP")
        # evaporator now
        #T_IN = fixed_points['T_IN_STORAGE_COLD'] - fixed_points['D_T_MIN']
        state_out_evap_sat = fluid_act.set_state(
            [p_low, 1.], "PQ")
        T_OUT_EVAP = state_out_evap_sat[0] + fixed_points['D_T_SUPER']
        state_out_evap = fluid_act.set_state(
            [p_low, T_OUT_EVAP], "PT")
        

    fixed_points["p_low"] = p_low
    fixed_points["p_high"] = p_high
    fixed_points['h_h_out_w']= state_out_cond[2]
    fixed_points['h_l_out_w']= state_out_evap[2]

    return fluid_act, fixed_points


def _extract_storage_values(data, storage_type):
    p_in = data[f'P_IN_{storage_type}']
    temp_in = data[f'T_IN_{storage_type}']
    temp_out = data[f'T_OUT_{storage_type}']
    return p_in, temp_in, temp_out


def read_hp_results(filename=_RESULTS_ +
                    "\\last_T_H_dot_plot_hp_evaluation_dict.npy"):
    """
    Reading the evaluation results dictionary of the heat pump

    Parameters
    ----------
    filename : string, optional
        name of the numpy file. The default is _RESULTS_+"\\last_T_H_dot_plot_hp".

    Returns
    -------
    loaded_dict : dictionary
        the saved results.

    """
    loaded_dict = np.load(filename,
                          allow_pickle=True).item()
    return loaded_dict


class HpVal(Serializable):
    """
    Class to store and read the *input* dictionary values and variables for a heat pump.

    Best is to set them in a yaml or json file and read them with the appropriate
    function. The default place to search for hp-input-dictvariables is in the
    data directory.

    Part of carbatpy.
    """
    default_path = DEFAULT_DIR
    default_filename = DEFAULT_FILE+".json"
    default_storage_filename = DEFAULT_FILE+"_last.json"

    def __init__(self, variables_dict=None):
        if variables_dict:
            for key, value in variables_dict.items():
                setattr(self, key, value)



if __name__ == "__main__":

    changes_here =False
    try: # which input file shall be used? example
        fn0= cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\hp-input-dict_opt_px.json"

        inputs = HpVal.load_from_file(fn0)
    except: # default value
        inputs = HpVal.load_from_file()

    INPUTS = inputs.to_dict()
    if changes_here:
        INPUTS["fluids_all"] =fluids_all
        p_select = {"optimize": None, "setting": "auto", "p_low": 0., "p_high": 0.0}
        INPUTS["P_WORKING"] = p_select
        # INPUTS["fluids_all"] = fluids_all
        new=HpVal(INPUTS)
        new.save_to_file(DEFAULT_FILE+".yaml")
        new.save_to_file(DEFAULT_FILE+".json")




    hpn = HeatPump( INPUTS)

    cop_n = hpn.calc_heat_pump(verbose=True)
    hpn.hp_plot()
    print(hpn.evaluation, hpn.components["condenser"]['dt_mean'])
    directory =cb.CB_DEFAULTS["General"]["RES_DIR"]
    filename = directory+"\\hp_normal.yml"
    hpn.save_to_file(filename)


    #---------------------------------


    my_dict = read_hp_results(_RESULTS_ +
                              "\\last_T_H_dot_plot_hp_evaluation_dict.npy")
