# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 12:35:02 2024

@author: atakan
"""
import json
import yaml
import carbatpy as cb

input_hp = {
    'process': {
        "compressor": "Flow_device",
        "condenser": "StaticHeatExchanger",
        "throttle": "Flow_device",
        "evaporator": "StaticHeatExchanger",

    },
    "species_all": {'working_fluid': "cycle",
               'cold_storage': "source-sink",
               'hot_storage': "source-sink",
               },
    'compressor': {
        "calc_type": "const_eta",
        "eta_s": 0.7,
        "species": {"working_fluid":{"in": "evaporator",
                                   "out":"condenser"},},
        "dt_superheat": 5,
        
    },
    'throttle': {
        "calc_type": "const_h",
        "species": {"working_fluid":{"in": "condenser" ,
                                   "out":"evaporator"},},
    },
    'condenser': {
        "calc_type": "const",
        "species": {"working_fluid":{"in":"compressor",
                                   "out":"throttle"}, 
                  "hot_storage":{"in":"temp_low",
                                 "out":"temp_high"}},
        "dt_min": 3.,

    },
    'evaporator': {
        "calc_type": "const",
        "species": {"working_fluid":{"in":"throttle",
                                   "out":"compressor"}, 
                  "cold_storage":{"in":"temp_high",
                                 "out":"temp_low"}},
        "dt_min": 3.,
    },
    'cold_storage': {
        "species": "Methanol",
        "fractions": [1.0],
        "p_low": 5e5,
        "temp_low": 250.0,
        "temp_high": "ambient"
    },
    'hot_storage': {
        "species": "Water",
        "fractions": [1.0],
        "p_low": 2e5,
        "temp_low": "ambient",
        "temp_high": 360.0
    },
    'working_fluid': {
        "species": "Propane * Butane * Pentane * Hexane",
        "fractions": [
            7.71733787e-01,
            2.22759488e-02,
            1.78685867e-01,
            0.027304397199999997],
        
        "temp_low": "ambient",
        "temp_high": 360.0,
        "p_low": 1.28250708e+05,
        "p_high": 1.37548728e+06,

        "optimize": "None",
        "setting": "initial",
        
    },
}


input_hex = {
    
    'condenser': {
        
        'model': "StaticHeatExchanger",
        "calc_type": "const",
        "species": {"working_fluid":{"in":"temp_high",
                                   "out":"temp_low"}, 
                  "hot_storage":{"in":"temp_low",
                                 "out":"temp_high"}},
        "dt_min": 3.,
        "q_dot": 1000.,
        "overall_u":100,
        'area': 1,

    },
    'hot_storage': {
        "species": "Water",
        "fractions": [1.0],
        "p_low": 2e5,
        "temp_low": "ambient",
        "temp_high": 360.0,
        'props':"REFPROP",
        
    },
    'working_fluid': {
        "species": "Propane * Butane * Pentane * Hexane",
        "fractions": [
            7.71733787e-01,
            2.22759488e-02,
            1.78685867e-01,
            0.027304397199999997],
        
        "temp_low": "ambient",
        "temp_high": 360.0,
        "p_low": 1.28250708e+05,
        "p_high": 1.37548728e+06,

        "optimize": "None",
        "setting": "initial",
        'props':"REFPROP",
        
    },
}

class Val():
    """
    Class to store and read the *input* dictionary values and variables for a heat pump.

    Best is to set them in a yaml or json file and read them with the appropriate
    function. The default place to search for hp-input-dictvariables is in the
    data directory.

    Part of carbatpy.
    """

    def __init__(self, variables_dict=None):
        if variables_dict:
            for key, value in variables_dict.items():
                setattr(self, key, value)

    def to_file(self, fname=None):
        if fname:
            with open(fname, "w") as file:
                if fname.find("json") > 0:
                    json.dump(self.__dict__, file, indent=4)
                elif fname.find("yaml") > 0:
                    yaml.dump(self.__dict__, file)
                else:
                    raise NotImplementedError(f"File type not implemeted {fname}")
        else:
            print("No file name given")

    @classmethod
    def from_file(cls, fname=None):
        instance = cls.__new__(cls)
        if fname:
            with open(fname, "r") as file:
                if fname.find("json") > 0:
                    data = json.load(file)
                elif fname.find("yaml") > 0:
                    data = yaml.safe_load(file)
                else:
                    raise NotImplementedError(f"File type not implemeted {fname}")
            for key, value in data.items():
                setattr(instance, key, value)
        else:
            print("No file name given")
        return instance


def find_key(a_dict, fl_name, t_amb =cb.CB_DEFAULTS['General']["T_SUR"]):
    for key in a_dict["process"].keys():
        di2 = a_dict[key]
        if fl_name in di2["species"].keys():
            in_out = di2["species"][fl_name]
            t_both= {}
            for key, value in in_out.items():
                t_act=  a_dict[fl_name][value]
                if t_act =="ambient":
                    t_act = t_amb
                t_both[key]=t_act
            #T_in, T_out = a_dict[fl_name][in_out["in"]], a_dict[fl_name][in_out["out"]]
            return t_both


if __name__ == "__main__":
    
    
    RES_DIR = cb.CB_DEFAULTS["General"]["RES_DIR"]

    fn0 = RES_DIR + "\\test_input3.yaml"

    #     mein = Val(input_hp)

    actuell = Val(input_hp)
    actuell.to_file(fn0)
    neu = Val.from_file(fn0)
    print (f'{find_key(input_hp, "cold_storage")}, hot: {find_key(input_hp, "hot_storage")}')
    with open(fn0, "r") as file:
        if fn0.find("json") > 0:
            in_dict = json.load(file)
        elif fn0.find("yaml") > 0:
            in_dict = yaml.safe_load(file)
