# -*- coding: utf-8 -*-
"""
Base class for thermodynamic cycles
Created on Tue Jul 30 13:26:28 2024

@author: atakan
"""
import copy
import numpy as np
import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable

class Cycle(Serializable):
    def __init__(self, fixed_points, components=None, **kwargs):
        self.fixed_points = fixed_points
        self.components = components if components else {}
        self.kwargs =kwargs
        self.all_states = []
        self.m_dots = []
        self.warning = []
        self.evaluation = self.init_evaluation()

        self.specific_init()
        
    

    
    
    def set_fl_state(self, fluid_values, fixed_points, **kwargs):
        # Implementierung bleibt spezifisch für Unterklassen
        raise NotImplementedError("This method must be overridden in subclasses.")

    def get_fp_value(self, key):
        # Keine Unterscheidung nach "common", direkt aus fixed_points entnehmen
        value = self.fixed_points.get(key)
        if value is None:
            raise KeyError(f"{key} not found in the input data.")
        return value
    
    

    def calc_cycle(self):
        raise NotImplementedError("This method must be overridden in subclasses.")

    
    """"    
    def set_fl_state(self, fluid_values, fixed_points, **kwargs):
        # Initialize fluid
        fluid_act = cb.init_fluid(*fluid_values["common"]["fluids_all"]["value"]["WORKING"][1:])
        fl_type = fluid_values["common"]["fluids_all"]["value"]["WORKING"][0]

        # Set common state values
        d_t_min = fluid_values["common"]["D_T_MIN"]["value"]
        d_t_super = fluid_values["common"]["D_T_SUPER"]["value"]

        # Check if it's a storage type
        if "STORAGE" in fl_type:
            fluid_act, fixed_points = self._set_storage_fl_state(fl_type, fluid_act, fixed_points)
        else:
            fluid_act, fixed_points = self._set_working_fl_state(fl_type, fluid_act, fixed_points, fluid_values, d_t_min, d_t_super)

        return fluid_act, fixed_points
    
    def get_fp_value(self, key):
        # Attempt to fetch value from 'common' section first
        value = self.fixed_points.get("common", {}).get(key, {}).get("value")
        if value is None:
            # Attempt to fetch value from specific section (based on the instance type)
            if isinstance(self, HeatPump):
                value = self.fixed_points.get("heat_pump", {}).get(key)
            elif isinstance(self, ORC):
                value = self.fixed_points.get("orc", {}).get(key)
        if value is None:
            raise KeyError(f"{key} not found in the input data.")
        return value
    
    def init_fluids(self):
        for fll, ii in self.fluids_all.items():
            # Setze den Zustand der Fluide basierend auf den Fixpunkten
            self.fluids.append(self.set_fl_state([fll, *ii], self.fixed_points)[0])

    def _set_storage_fl_state(self, fl_type, fluid_act, fixed_points):
        p_in, t_in, t_out = self._extract_storage_values(fixed_points, fl_type)
        state_out = fluid_act.set_state([t_out, p_in], "TP")
        state_in = fluid_act.set_state([t_in, p_in], "TP")

        if "HOT" in fl_type:
            fixed_points['h_h_out_sec'] = state_out[2]
        elif "COLD" in fl_type:
            fixed_points['h_l_out_cold'] = state_out[2]

        return fluid_act, fixed_points

    def _set_storage_fl_state(self, fl_type, fluid_act, fixed_points):
        p_in, t_in, t_out = self._extract_storage_values(fixed_points, fl_type)
        state_out = fluid_act.set_state([t_out, p_in], "TP")
        state_in = fluid_act.set_state([t_in, p_in], "TP")

        if "HOT" in fl_type:
            fixed_points['h_h_out_sec'] = state_out[2]
        elif "COLD" in fl_type:
            fixed_points['h_l_out_cold'] = state_out[2]

        return fluid_act, fixed_points

    def _set_working_fl_state(self, fl_type, fluid_act, fixed_points, fluid_values, d_t_min, d_t_super):
        w_p_select = fluid_values.get("P_WORKING", {"setting": "initial"})
        if w_p_select["setting"] == "auto":
            fluid_act, fixed_points = self._auto_set_pressure(fluid_act, fixed_points, d_t_min, d_t_super)
        else:
            fluid_act, fixed_points = self._manual_set_pressure(fluid_act, fixed_points, w_p_select, d_t_min, d_t_super)

        return fluid_act, fixed_points

    def _auto_set_pressure(self, fluid_act, fixed_points, d_t_min, d_t_super):
        state_in_cond = fluid_act.set_state([fixed_points['T_OUT_STORAGE_HOT'], 1.], "TQ")
        p_high = state_in_cond[1]

        state_out_cond = fluid_act.set_state([fixed_points['T_IN_STORAGE_HOT'] + d_t_min, p_high], "TP")
        T_IN = fixed_points['T_IN_STORAGE_HOT'] - d_t_min
        state_satv_evap = fluid_act.set_state([T_IN - d_t_super, 1.], "TQ")
        p_low = state_satv_evap[1]

        state_out_evap = fluid_act.set_state([p_low, T_IN], "PT")

        fixed_points["p_low"] = p_low
        fixed_points["p_high"] = p_high
        fixed_points['h_h_out_w'] = state_out_cond[2]
        fixed_points['h_l_out_w'] = state_out_evap[2]

        return fluid_act, fixed_points

    def _manual_set_pressure(self, fluid_act, fixed_points, w_p_select, d_t_min, d_t_super):
        p_high = w_p_select.get("p_high", 0)
        p_low = w_p_select.get("p_low", 0)

        state_in_cond = fluid_act.set_state([fixed_points['T_OUT_STORAGE_HOT'], p_high], "TP")
        state_out_cond = fluid_act.set_state([fixed_points['T_IN_STORAGE_HOT'] + d_t_min, p_high], "TP")

        T_IN = fixed_points['T_IN_STORAGE_HOT'] - d_t_min
        state_satv_evap = fluid_act.set_state([T_IN - d_t_super, p_low], "TP")
        state_out_evap = fluid_act.set_state([p_low, T_IN], "PT")

        fixed_points["p_low"] = p_low
        fixed_points["p_high"] = p_high
        fixed_points['h_h_out_w'] = state_out_cond[2]
        fixed_points['h_l_out_w'] = state_out_evap[2]

        return fluid_act, fixed_points

    def _extract_storage_values(self, fixed_points, fl_type):
        # Extracts storage values for specific fluid type (hot/cold)
        if "HOT" in fl_type:
            p_in = fixed_points.get('P_IN_STORAGE_HOT', 0)
            t_in = fixed_points.get('T_IN_STORAGE_HOT', 0)
            t_out = fixed_points.get('T_OUT_STORAGE_HOT', 0)
        elif "COLD" in fl_type:
            p_in = fixed_points.get('P_IN_STORAGE_COLD', 0)
            t_in = fixed_points.get('T_IN_STORAGE_COLD', 0)
            t_out = fixed_points.get('T_OUT_STORAGE_COLD', 0)
        else:
            raise ValueError(f"Unknown storage type: {fl_type}")
        return p_in, t_in, t_out
    
     """   
    def calculate_hex(self, params, plot_info={}, verbose_=True):
        """
        General method for calculating a heat exchanger.

        params: dict containing the following keys:
            - fluid_numbers: List[int]
            - h_dot_min: float
            - h_out_w: float
            - h_limit_s: float (optional)
            - d_temp_separation_min: float (optional)
            - calc_type: str (optional)
            - pinch: str (optional)
            - name: str (optional)
        """
        fluid_numbers = params["fluid_numbers"]
        h_dot_min = params["h_dot_min"]
        h_out_w = params["h_out_w"]
        h_limit_s = params.get("h_limit_s", np.nan)
        d_temp_separation_min = params.get("d_temp_separation_min", 0.5)
        calc_type = params.get("calc_type", "const")
        pinch = params.get("pinch", "")
        name = params.get("name", "evaporator")

        w_actual, s_actual = [self.fluids[fluid_numbers[0]],
                              self.fluids[fluid_numbers[1]]]
        hex_act = cb.hex_th.StaticHeatExchanger(
            [w_actual, s_actual],
            h_dot_min, h_out_w, h_limit_s,
            d_temp_separation_min=d_temp_separation_min,
            name=name
        )

        if pinch == "":
            h_s_out = hex_act.pinch_calc(plot_info)
        elif pinch == "secondary":
            h_s_out = hex_act.find_pinch()
        elif pinch == "working":
            h_s_out = hex_act.find_pinch(False)
        else:
            print("calculate_hex: This option is not available")

        if hex_act.warning > 0:
            print("Heat-Exchanger problem: ", hex_act.warning, hex_act.warning_message)
            self.warning.append([hex_act.name, hex_act.warning, hex_act.warning_message])
        
        m_dot_s, d_tempall, wf_states, sf_states = hex_act.pinch_plot(plotting=verbose_)
        d_temp_mean = hex_act.dt_mean
        d_temp_min = hex_act.dt_min

        self.all_states.append(wf_states)
        self.all_states.append(sf_states)
        self.m_dots.append(hex_act.m_dot_w)
        self.m_dots.append(m_dot_s)

        w_after_hex = self.fluids[0].set_state([wf_states[0, 1], wf_states[0, 2]], "PH")
        fluids_states_in_out = np.array([[wf_states[0], wf_states[-1]], [sf_states[0], sf_states[-1]]])
        fluids_states_in_out_ex = fluids_states_in_out
        if hex_act.heating < 1:
            fluids_states_in_out_ex = np.flip(fluids_states_in_out, axis=1)

        mass_flow_rates = np.array([hex_act.m_dot_w, hex_act.m_dot_s])
        ex_loss_rate = cb.exlo.exergy_loss_flow(fluids_states_in_out_ex, mass_flow_rates)
        
        self.evaluation[name] = {
            "states-in-out": fluids_states_in_out,
            "mass-flow-rates": mass_flow_rates,
            "exergy-loss-rate": ex_loss_rate,
            "dT-min": d_temp_min,
            "dT-mean": d_temp_mean
        }
        self.components[name] = hex_act.all
        
        if verbose_:
            print(f"After heat exchanger: {name}")
            w_actual.print_state()
        
        return w_after_hex

          
    

    

    def plot(self, f_name, fig_ax=[]):
        # Gemeinsame Plot-Methode
        pass

    # Weitere gemeinsame Methoden und Attribute


class HeatPump(Cycle):
    def __init__(self, components=None, fixed_points=None, fluids=None, **kwargs):
        super().__init__(components=components, fixed_points=fixed_points, **kwargs)
        # Additional initializations specific to HeatPump
        self.fluids_all = fixed_points.get("fluids_all", {})
        self.fluids = []
        super().__init__(fixed_points, components)
        self.init_fluids()
        
    def init_evaluation(self):
       # Definition der spezifischen Evaluationsattribute für HeatPump
       return {
           "Q_DOT_MIN": self.fixed_points["common"]["Q_DOT_MIN"],
           "Power": 0.0,
           "T_OUT_STORAGE_HOT": self.fixed_points["common"]["T_OUT_STORAGE_HOT"],
           "T_OUT_STORAGE_COLD": self.fixed_points["common"]["T_OUT_STORAGE_COLD"],
           "exergy_loss_rate": 0
       }

    def specific_init(self):
        # Zusätzliche Initialisierungen für HeatPump
        pass
    
    def _set_working_fl_state(self, fl_type, fluid_act, fixed_points):
        # If HeatPump has a specific way of setting working fluid states
        return super()._set_working_fl_state(fl_type, fluid_act, fixed_points)
    
    

    def calc_cycle(self, plot_info={}, variations=["", ""], verbose=False):
        """
        Calculates a simple compression heat pump cycle.
        """
        state_in = copy.copy(self.fluids[0])
        w_actual = self.fluids[0]
        if verbose:
            print("Start:")
            w_actual.print_state()

        # Compressor
        compressor = cb.FlowDevice(
            self.fluids[0], self.fixed_points["p_high"], 1.0,
            device_type="machine", name="compressor",
            calc_type="const_eta", calc_parameters={"eta_s": self.fixed_points["ETA_S_C"]},
            plot_info=plot_info
        )
        w_after_compressor, work_c, _power = compressor.state_w_p()
        self.components[compressor.name] = compressor.all
        
        if verbose:
            print("After the compressor")
            w_actual.print_state()

        # Condenser
        params = {
            "fluid_numbers": [0, 1],
            "h_dot_min": self.fixed_points["Q_DOT_MIN"],
            "h_out_w": self.fixed_points["h_h_out_w"],
            "h_limit_s": self.fixed_points["h_h_out_sec"],
            "d_temp_separation_min": self.fixed_points['D_T_MIN'],
            "calc_type": variations[0],
            "name": "condenser"
        }
        w_after_condenser = self.calculate_hex(params, plot_info=plot_info, verbose_=verbose)

        power = work_c * self.m_dots[params["fluid_numbers"][0]]
        heat_flow_evap = self.fixed_points["Q_DOT_MIN"] - power
        if verbose:
            print(f"Power: {power} W, Evaporator heat: {heat_flow_evap} W\n")

        # Throttle
        throttle = cb.FlowDevice(
            w_actual, self.fixed_points["p_low"], self.m_dots[params["fluid_numbers"][0]],
            device_type="throttle", name="throttle-A", calc_type="const_h", calc_parameters={},
            plot_info=plot_info
        )
        w_after_throttle = throttle.output["state_out"]
        self.components[throttle.name] = throttle.all

        if verbose:
            print("After the throttle:")
            print(w_actual.print_state())

        w_act = w_actual.set_state([w_after_throttle[1], w_after_throttle[2]], "PH")
        if self.fixed_points["T_OUT_STORAGE_COLD"] < w_act[0] + self.fixed_points['D_T_MIN']:
            self.fixed_points["T_OUT_STORAGE_COLD"] = w_act[0] + self.fixed_points['D_T_MIN']

        # Evaporator
        params = {
            "fluid_numbers": [0, 2],
            "h_dot_min": heat_flow_evap,
            "h_out_w": self.fixed_points["h_l_out_w"],
            "h_limit_s": self.fixed_points["h_l_out_cold"],
            "d_temp_separation_min": self.fixed_points['D_T_MIN'],
            "calc_type": variations[0],
            "name": "evaporator"
        }
        w_after_evap = self.calculate_hex(params, plot_info=plot_info, verbose_=verbose)

        q_evap = (w_after_evap[2] - w_after_throttle[2]) * self.m_dots[params["fluid_numbers"][0]]
        if heat_flow_evap - q_evap > 1:
            print(f"Heat pump cycle not in equilibrium: {heat_flow_evap}, {q_evap}")

        if verbose:
            print(f"Evaporator heat flow rate: {q_evap}, Power: {power}")
            w_actual.print_state()

        # Calculate exergy losses
        sec_fluids_states_in_out = np.array([
            self.evaluation["condenser"]["states-in-out"][-1],
            self.evaluation["evaporator"]["states-in-out"][-1]
        ])
        mass_flow_rates = np.array([
            self.evaluation["condenser"]["mass-flow-rates"][-1],
            self.evaluation["evaporator"]["mass-flow-rates"][-1]
        ])
        ex_loss_rate = cb.exlo.exergy_loss_flow(sec_fluids_states_in_out, mass_flow_rates)

        cop = self.fixed_points["Q_DOT_MIN"] / power
        self.evaluation.update({
            "Q_DOT_MIN": self.fixed_points["Q_DOT_MIN"],
            "Power": power,
            "p_high": self.fixed_points["p_high"],
            "p_low": self.fixed_points["p_low"],
            "exergy_loss_rate": ex_loss_rate,
            "sec_fluid_states_in_out": sec_fluids_states_in_out,
            "sec_fluid_m_dots": mass_flow_rates,
            "COP": cop
        })
        return cop

    # def calculate_hex(self, fluid_numbers, h_dot_min_, h_out_w_, h_limit_s_=float('nan'), points_=50, d_temp_separation_min_=0.5, calc_type_='const', pinch='', name_='evaporator', plot_info={}, verbose_=True):
    #     # Weitere spezifische Methode
    #     pass


class OrganicRankineCycle(Cycle):
    def __init__(self, components=None, fixed_points=None, fluids=None, **kwargs):
        super().__init__(components=components, fixed_points=fixed_points, fluids=fluids, **kwargs)
        # Additional initializations specific to ORC
        
        self.fluids_all = fixed_points.get("fluids_all", {})
        self.fluids = []
        super().__init__(fixed_points, components)
        self.init_fluids()
        
    def init_evaluation(self):
        # Definition der spezifischen Evaluationsattribute für ORC
        return {
            "Q_DOT_MIN": self.fixed_points["Q_DOT_MIN"],
            "Power-Net": 0.0,
            "T_hh": self.fixed_points["T_OUT_STORAGE_HOT"], #reversed reative to heat pump
            "T_ll": self.fixed_points["T_OUT_STORAGE_COLD"],
            "eta_pc": 0
        }

    def specific_init(self):
        # Zusätzliche Initialisierungen für ORC
        pass
    
    def _set_working_fl_state(self, fl_type, fluid_act, fixed_points):
        # If ORC has a specific way of setting working fluid states
        return super()._set_working_fl_state(fl_type, fluid_act, fixed_points)
    
    def calc_cycle(self, verbose=False):
        """
        Calculates a simple Organic Rankine Cycle (ORC).
        """
        state_in = copy.copy(self.fluids[0])
        w_actual = self.fluids[0]
        if verbose:
            print("Start:")
            w_actual.print_state()

        # Pump
        pump = cb.FlowDevice(
            self.fluids[0], self.fixed_points["p_high"], 1.0,
            device_type="pump", name="pump",
            calc_type="const_eta", calc_parameters={"eta_s": self.fixed_points["eta_s_p"]}
        )
        w_after_pump, work_pump, _power = pump.state_w_p()
        m_dot_w = self.fixed_points["Q_DOT_MIN"] / (self.fixed_points["h_out_w"] - w_after_pump[2])
        self.components[pump.name] = pump.all

        if verbose:
            print("After the pump")
            w_actual.print_state()

        # Evaporator
        params = {
            "fluid_numbers": [0, 1],
            "h_dot_min": self.fixed_points["Q_DOT_MIN"],
            "h_out_w": self.fixed_points["h_out_w"],
            "d_temp_separation_min": self.fixed_points["D_T_MIN"],
            "calc_type": self.fixed_points["Q_DOT_MIN"],
            "name": "evaporator"
        }
        w_after_evaporator = self.calculate_hex(params, verbose_=verbose)

        # Expander
        expander = cb.FlowDevice(
            self.fluids[0], self.fixed_points["p_low"], m_dot_w,
            device_type="machine", name="expander",
            calc_type="const_eta", calc_parameters={"eta_s": self.fixed_points["eta_s_e"]}
        )
        w_after_expander, work_expander, _power = expander.state_w_p()
        self.components[expander.name] = expander.all

        if verbose:
            print("After the expander")
            w_actual.print_state()

        # Condenser
        params = {
            "fluid_numbers": [0, 2],
            "h_dot_min": self.fixed_points["Q_DOT_MIN"],
            "h_out_w": self.fixed_points["h_out_c"],
            "d_temp_separation_min": self.fixed_points["D_T_MIN"],
            "calc_type": self.fixed_points["Q_DOT_MIN"],
            "name": "condenser"
        }
        w_after_condenser = self.calculate_hex(params, verbose_=verbose)

        # Net work and efficiency
        work_net = work_expander - work_pump
        eta = work_net / self.fixed_points["Q_DOT_MIN"]

        self.evaluation.update({
            "NetWork": work_net,
            "p_high": self.fixed_points["p_high"],
            "p_low": self.fixed_points["p_low"],
            "Efficiency": eta
        })
        return eta


import json
"""abrik-Muster für die Erzeugung von Kreisprozessen

Ein Fabrik-Muster kann genutzt werden, um basierend auf einer Konfigurationsdatei oder Parameterinstanz den entsprechenden Kreisprozess zu erstellen"""


class CycleFactory:
    @staticmethod
    def create_cycle(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        cycle_type = config.get('type')
        fixed_points = config.get('fixed_points')
        components = config.get('components', [])

        if cycle_type == 'HeatPump':
            return HeatPump(fixed_points, components)
        elif cycle_type == 'OrganicRankineCycle':
            fluids = config.get('fluids')
            return OrganicRankineCycle(fluids, fixed_points, components)
        else:
            raise ValueError(f"Unknown cycle type: {cycle_type}")


""" config.json
{
    "type": "HeatPump",
    "fixed_points": [300, 350],
    "components": ["compressor", "condenser"],
    "plot_info": {}
}

"""

if __name__ =="__main__":
    import json
    file_n = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\input_hp_orc_unified.json"
    with open(file_n, "r") as file:
        inp_hp = json.load(file)
        
    file_n = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\orc_input.json"
    with open(file_n, "r") as file:
        inp_orc = json.load(file)
        
    hp_act =HeatPump(fixed_points=inp_hp)
    hp_act.calc_cycle()
    
    orc_act =OrganicRankineCycle(fixed_points=inp_hp)
    orc_act.calc_cycle()