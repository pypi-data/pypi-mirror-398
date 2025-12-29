# -*- coding: utf-8 -*-
"""

Created on Sun Aug  4 09:44:00 2024

@author: atakan
"""


import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable, DataAll, DataNode
import json
import yaml


def read_config(file_path):
    if isinstance(file_path,dict):
        return file_path

    if file_path.endswith('.yaml') or file_path.endswith('.yml'):
        return read_yaml(file_path)
    elif file_path.endswith('.json'):
        return read_json(file_path)
    else:
        raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")


def read_yaml(file_path):
    import yaml
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def read_json(file_path):
    import json
    with open(file_path, 'r') as file:
        return json.load(file)


def fluid_from_dict_file(fluid_name, path_dict, **kwargs):
    info = path_dict
    if isinstance(path_dict, str):
        info = read_config(path_dict)
    fluid_act = info.get(fluid_name)

    fl_instance = cb.init_fluid(fluid_act["species"],
                                fluid_act["fractions"],
                                props=fluid_act["props"])
    return fl_instance


def read_component(config_dict, name=None, temp_ambient=None):
    parsed_components = {}
    if isinstance(config_dict, str):
        config_dict = read_config(config_dict)
    if name:
        parsed_component = parse_equipment(
            name, config_dict[name], config_dict, temp_ambient)
        return parsed_component
    else:

        for name, config in config_dict.items():
            if "model" in config:
                parsed_components[name] = parse_equipment(
                    name, config, config_dict, temp_ambient)
        return parsed_components


def parse_equipment(name, config, config_all, temp_ambient):
    model = config['model']
    parameters = config.get('parameters')
    calc_type = config.get('calc_type')
    species = config.get('species', {})
    dtemp_min = config.get("dt_min")
    if "low" in species['working_fluid']['in']:
        dtemp_min = -parameters["dt_min"]
    states = {}

    act_fluids = {}

    for fluid, flow in species.items():
        act_fluids[fluid] = fluid_from_dict_file(fluid, config_all)
        fl = config_all[fluid]
        pressure = fl["p_low"]
        states[fluid] = {}
        for where in ["out", "in"]:
            # if not temperatures are prescribed, but other components, no states are calculated
            if "temp" in flow[where]:
                if flow[where] =="temp_start": # determine an initial state, if not given. Changes/sets pressure!
                    states[fluid][where]  = _get_start(config_all, 
                                                       act_fluids[fluid],
                                                       species,
                                                       temp_ambient)
                    
                # BA 2025-07-28: second posibility "temp_start_tp" for fixing temp and p? Superheating must then be checked independently. Could be better for optimizations.    
                else:
                    temp = fl[flow[where]] if where in flow else None
                    if temp == 'ambient':
                        temp = cb.CB_DEFAULTS["General"]["T_SUR"]
                        if temp_ambient:
                            temp = temp_ambient
                    if where == "out" and "working" in fluid:
                        temp += dtemp_min  # BA looks dangerous 2024-08-15
    
                    states[fluid][where] = act_fluids[fluid].set_state(
                            [temp, fl[flow["p_" + where]]], "TP")
            else:
                states[fluid][where] = flow[where]
                # will be calculated along cycle

        
        

    return {
        'name': name,
        'model': model,
        'calc_type': calc_type,
        'states': states,
        'act_fluids': act_fluids,
        'parameters': {k: v for k, v in config.items() if k not in ['model', 'calc_type', 'species']}
    }


def _get_start(config, fluid_act, which, temp_ambient):
    """
    Calculate starting points for cycles, when not given otherwise.
    
    Only for heat pumps so far. Evaporator outlet should be superheated by a given
    value and have a minimum distance to the entering storage fluid.
    
    

    Parameters
    ----------
    config : dictionary
        the whole cycle configuration.
    fluid_act : Fluid
        the working fluid (model) to set its state. This input state is changed!
    which : dictionary
        with both fluid-species names, to find the non-working-fluid.
    temp_ambient : TYPE
        if this is the value of the storage.

    Raises
    ------
    NotImplementedError
        DESCRIPTION.

    Returns
    -------
    FluidState
        the state of the starting point.
    state_sh : TYPE
        DESCRIPTION.

    """
    if config["process"]["name"]=="heat_pump":
        keys = list(which.keys()  ) 
        for key in keys:
            if key != 'working_fluid':
                other_key = key
                break
        temp_key = which[other_key]["in"]
        temp =  _set_temp(config[other_key][temp_key], temp_ambient)
        temp_sat =temp - config["start"]["dt_min"]- config["start"]["dt_superheat"]
        
        sat = fluid_act.set_state([temp_sat,1],"TQ")
        temp_sh = temp - config["start"]["dt_min"]
        n_pres =cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'].index("Pressure")
        
        state_sh = fluid_act.set_state([temp_sh, sat[n_pres]],"TP")
        return state_sh 
    
    elif config["process"]["name"].lower() in ("organic_rankine_cycle", "orc"):
        keys = list(which.keys()  ) 
        for key in keys:
            if key != 'working_fluid':
                other_key = key
                break
        temp_key = which[other_key]["in"]
        temp =  _set_temp(config[other_key][temp_key], temp_ambient)
        temp_sat = temp + config["start"]["dt_min"] + config["start"]["dt_subcool"]
        p_low =config["working_fluid"]["p_low"]
        
        sat = fluid_act.set_state([p_low,0],"PQ")
        temp_sh =sat[0] -  config["start"]["dt_subcool"]
        if temp_sh < temp_sat:
            temp_sh = temp + config["start"]["dt_min"]
        n_pres = cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'].index("Pressure")
        
        state_sh = fluid_act.set_state([temp_sh, sat[n_pres]],"TP")
        return state_sh 
        
    else:
        raise NotImplementedError("other cycles are not implemented yet (starting point)")
        
        
def _set_temp(temp, temp_ambient =None):
    """
    Set the ambient temperature when temp ='ambient'.
    

    Parameters
    ----------
    temp : TYPE
        DESCRIPTION.
    temp_ambient : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    temp : TYPE
        DESCRIPTION.

    """
    if temp == 'ambient':
        temp = cb.CB_DEFAULTS["General"]["T_SUR"]
        if temp_ambient:
            temp = temp_ambient
    return temp


def setup_system(config_path):
    config = config_path
    if isinstance(config_path, str):

        config = read_config(config_path)

    # Komponenten einlesen
    components = read_component(config)

    # Fluide einlesen
    fluids = {}
    for name, fluid_config in config.items():
        if "props" in fluid_config:
            fluids[name] = fluid_from_dict_file(name, config)

    return components, fluids


if __name__ == "__main__":
    input_hex = {
        'process': {"cycle": ["start",
                              "compressor",
                              "condenser",
                              "throttle",
                              "evaporator",
                              "start"],
                    "name": "heat_pump",
                    },

        'fluids_all': {'working_fluid': 'cycle',
                       'cold_storage': 'source-sink',
                       'hot_storage': 'source-sink'
                       },
        'start': {
            'model': "Start",
            "calc_type": None,
            "species": {"working_fluid": {"in": "temp_start",
                                          "out": "temp_start",
                                          "p_in": "p_low",
                                          "p_out": "p_low"},
                        "cold_storage": {"in": "temp_high",
                                        "out": "temp_high",
                                        "p_in": "p_low",
                                        "p_out":"p_low"}},
            "dt_min": 3.,
            "dt_superheat": 5.,
            
        },

        'compressor': {
            'model': "FlowDevice",
            'calc_type': 'const_eta',
            'eta_s': 0.7,
            'fixed': 'power',
            'power': 1000.,
            'species': {'working_fluid': {'in': 'evaporator',
                                          'out': 'condenser',
                                          "p_in": "p_low",
                                          "p_out": "p_high"}},
            'dt_superheat': 5
        },

        'throttle': {
            'model': "FlowDevice",
            'calc_type': 'const_h',
            'fixed': "m_dot",
            'species': {'working_fluid': {'in': 'condenser',
                                          'out': 'evaporator',
                                          "p_in": "p_high",
                                          "p_out": "p_low"}}
        },



        'condenser': {
            'model': "StaticHeatExchanger",
            "calc_type": "const",
            'fixed': "m_dot_w",
            "species": {"working_fluid": {"in": "temp_high",
                                          "out": "temp_low",
                                          "p_in": "p_high",
                                          "p_out": "p_high"},
                        "hot_storage": {"in": "temp_low",
                                        "out": "temp_high",
                                        "p_in": "p_low",
                                        "p_out":"p_low"}},
            "dt_min": 3.,
            "q_dot": 1000.,
            "overall_u": 100,
            'area': 1,
        },

        'evaporator': {
            'model': "StaticHeatExchanger",
            'calc_type': 'const',
            'fixed': "m_dot_w",
            'species': {'working_fluid': {'in': 'throttle',
                                          'out': 'compressor',
                                          "p_in": "p_low",
                                          "p_out":"p_low"},
                        'cold_storage': {'in': 'temp_high',
                                         'out': 'temp_low',
                                         "p_in": "p_low",
                                         "p_out":"p_low"}},
            'dt_min': 3.0,
            
            "overall_u": 100,
            'area': 1,
        },

        'hot_storage': {
            "species": "Water",
            "fractions": [1.0],
            "p_low": 2e5,
            "temp_low": "ambient",
            "temp_high": 370.0,
            'props': "REFPROP",
            
            'fixed': None,
        },


        'cold_storage': {
            "species": "Methanol",
            "fractions": [1.0],
            "p_low": 2e5,
            "temp_low": 255.0,
            "temp_high": "ambient",
            'props': "REFPROP",
            'fixed': None,
        },
        'working_fluid': {
            "species": "Propane * Butane * Pentane * Hexane",
            "fractions": [
                7.71733787e-01,
                2.22759488e-02,
                1.78685867e-01,
                0.027304397199999997],
            "temp_low": "ambient",
            "temp_high": 420.0,
            "p_low": 1.128250708e+05,
            "p_high": 1.37548728e+06,
            "optimize": "None",
            "setting": "initial",
            'props': "REFPROP",
        },
    }

    act_fl = fluid_from_dict_file("working_fluid", input_hex)
    act_fl.set_state([300, 1e5], "TP")
    act_fl.print_state()
    # aa = setup_system(input_hex)
    # print("\n", aa)
    start = read_component(input_hex, "start")
    compressor = read_component(input_hex, "compressor")
    condenser = read_component(input_hex, "condenser")
    p_names =cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names']
    n_temp= p_names.index("Temperature")
    n_pres =p_names.index("Pressure")
    print( condenser["states"]["working_fluid"]["in"][n_temp],
          condenser["states"]["working_fluid"]["out"][n_temp],
          condenser["states"]["working_fluid"]["in"][n_pres])
    fn = cb.CB_DEFAULTS["General"]["RES_DIR"]+"\\io-cycle-data2.yaml"
    
    with open(fn, "w") as file:
        yaml.safe_dump(input_hex, file)
