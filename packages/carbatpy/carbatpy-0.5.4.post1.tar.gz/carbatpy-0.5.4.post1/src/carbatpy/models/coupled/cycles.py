# -*- coding: utf-8 -*-
"""
cycle calculation one input for each cyle
Created on Wed Jul 31 17:01:59 2024

@author: atakan
"""
import copy
import numpy as np
import matplotlib.pyplot as plt
import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable


class Cycle:
    def __init__(self, components=None, fixed_points=None,  **kwargs):
        self.components = components if components else {}
        self.fixed_points = fixed_points
        
        self.all_states = []
        self.m_dots = []
        self.evaluation = {}
        self.warning = []
        self.kwargs = kwargs
        
        self.fluids_all = copy.copy(fixed_points["fluids_all"])
        self.fluids = []
        self.set_fl_state()

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

    def calc_cycle(self):
        raise NotImplementedError("This method must be overridden in subclasses.")
        
    def plot(self):
        raise NotImplementedError("This method must be overridden in subclasses.")
        
class HeatPump(Cycle):
    def __init__(self, components=None, fixed_points=None, **kwargs):
        super().__init__(components=components, fixed_points=fixed_points, kwargs=kwargs)
        # Additional initializations specific to HeatPump
        
        
    def set_fl_state(self,
                      **kwargs):
        
        fluids =  {}
        p_all= {}
        for key in self.fluids_all.keys():
            fluids[key] = cb.init_fluid(self.fixed_points[key]["fluid"],
                                      self.fixed_points[key]["composition"],
                                      kwargs=self.fixed_points[key]) # props etc. cn be passed here
            
            p_all[key]= self.fixed_points[key]["p_low"]
            
        for compound in self.fixed_points["process"].keys():
            if compound =="compressor":
                dt_sup = self.fixed_points[compound]["dt_superheat"]
            elif compound =="throttle":
                pass
            elif compound == "condenser":
                t_in_out = self._find_st_in_out(compound)
                dt = self.fixed_points[compound]["dt_min"]
                for fl_act in self.fixed_points[compound]["fluid"].keys():
                    if "storage" in fl_act:
                        state_out = fluids[fl_act].set_state([t_in_out['out'], p_all[fl_act]], "TP")
                        state_in = fluids[fl_act].set_state([t_in_out['in'], p_all[fl_act]], "TP")
                        self.fixed_points['h_h_out_sec'] = state_out[2]
                    else:
                        state_out = fluids[fl_act].set_state([t_in_out['out']+dt, p_all[fl_act]], "TP")
                        
                
                            
            
        #     if "storage" in key:
        #         p_in = self.fixed_points[key]["p_low"]
        #         t_in_out =t_val["hot_storage"] # Default T_sur is used!
        #         state_out = fluid_act.set_state([t_in_out['out'], p_in], "TP")
        #         state_in = fluid_act.set_state([t_in_out['in'], p_in], "TP")
    
        #         if "hot" in key:
        #             self.fixed_points['h_h_out_sec'] = state_out[2]
                    
        #         elif "cold" in key:
        #             self.fixed_points['h_l_out_cold'] = state_out[2]
    
                    
    
        #     w_p_select = self.fixed_points["working_fluid"]
        #     if w_p_select["setting"]== "auto":
        #         temp_high= self.fixed_points['hot_storage']["temp_high"]
        #         state_in_cond = fluid_act.set_state(
        #             [temp_high, 1.], "TQ")  # find high pressure
        #         p_high = state_in_cond[1]
    
        #         state_out_cond = fluid_act.set_state([temp_high +
        #                                             self.fixed_points["condenser"]['dt_min'],
        #                                             p_high], "TP")
                
        #         T_IN = t_val["evaporator"] - fixed_points['D_T_MIN']
        #         state_satv_evap = fluid_act.set_state(
        #             [T_IN -
        #              fixed_points['D_T_SUPER'], 1.], "TQ")  # find minimum pressure
        #         p_low = state_satv_evap[1]
    
        #         state_out_evap = fluid_act.set_state([p_low,
        #                                             T_IN], "PT")
        #     else:
        #         p_high =  w_p_select["p_high"]
        #         p_low =  w_p_select["p_low"]
        #         state_in_cond = fluid_act.set_state(
        #             [fixed_points['T_OUT_STORAGE_HOT'],p_high], "TP")  # find high pressure
    
    
        #         state_out_cond = fluid_act.set_state([fixed_points['T_IN_STORAGE_HOT'] +
        #                                             fixed_points['D_T_MIN'],
        #                                             p_high], "TP")
        #         T_IN = fixed_points['T_IN_STORAGE_HOT'] - fixed_points['D_T_MIN']
        #         state_satv_evap = fluid_act.set_state(
        #             [T_IN -
        #              fixed_points['D_T_SUPER'], p_low], "TP")  # find minimum pressure
    
        #         state_out_evap = fluid_act.set_state([p_low,
        #                                             T_IN], "PT")
    
        #     fixed_points["p_low"] = p_low
        #     fixed_points["p_high"] = p_high
        #     fixed_points['h_h_out_w']= state_out_cond[2]
        #     fixed_points['h_l_out_w']= state_out_evap[2]
        #     self.fluids.append(fluid_act)
        # return fluids_act, fixed_points
    
    
    
    
    def _find_st_in_out(self, what,  t_amb =cb.CB_DEFAULTS['General']["T_SUR"]):
        
        for key in self.fixed_points[what]["fluid"]:
            if "storage" in key:
                fl_name = self.fixed_points[what]["fluid"]
                
    
            # for key in self.fixed_points["process"].keys():
            #     di2 = self.fixed_points[key]
                if fl_name in di2["fluid"].keys():
                    in_out = di2["fluid"][fl_name]
                    t_both= {}
                    for key, value in in_out.items():
                        t_act=  self.fixed_points[fl_name][value]
                        if t_act =="ambient":
                            t_act = t_amb
                        t_both[key]=t_act
                
                return t_both
    def _get_all_t(self):
        t_values={}
        for key in self.fixed_points:
            if "storage" in key:
                t_b = self._find_st_in_out(key)
                t_values[key]=t_b
        t_values["d_super"]=self.fixed_points["compressor"]["dt_superheat"]
        t_values["dt_min_cond"]=self.fixed_points["coondenser"]["dt_min"]
        t_values["dt_min_evap"]=self.fixed_points["evaporator"]["dt_min"]
        return t_values
                    
    

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
    
    def plot(self, f_name=None, **kwargs):
    
        """
        plots the heat pump cycle and stores it to the given file (name)
    
        Returns
        -------
        None.
    
        """
        if not f_name:
            f_name =cb.CB_DEFAULTS["General"]["RES_DIR"]+"\\last_T_H_dot_plot_hp"
        if kwargs:
            print(f"keyword argumnts not implemented in hp-plot, will be ignored{kwargs}")
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


class ORC(Cycle):
    def __init__(self, components=None, fixed_points=None, fluids=None):
        super().__init__(components, fixed_points, fluids)
        # Additional initializations specific to ORC

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


if __name__ =="__main__":
    import json
    file_n = cb.CB_DEFAULTS["General"]["RES_DIR"]+"\\test_input3.json"
    with open(file_n, "r") as file:
        inp_hp = json.load(file)
        
    file_n = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\orc_input.json"
    with open(file_n, "r") as file:
        inp_orc = json.load(file)
        
    hp_act =HeatPump(fixed_points=inp_hp)
    hp_act.calc_cycle()
    hp_act.plot()