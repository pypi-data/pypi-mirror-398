# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 15:28:50 2024

@author: atakan
"""
class StaticHeatExchanger:
    def __init__(self, fluids, h_dot_min, h_out_w, h_limit_s, **kwargs):
        self.fluids = fluids
        state_in_w = fluids[0].properties.state
        self.m_dot_s = 0
        self.h_limit_s = h_limit_s
        self.q_dot = h_dot_min
        self.m_dot_w = np.abs(h_dot_min / (h_out_w - state_in_w[2]))
        self.h_out_w = h_out_w
        self.h_out_s = float(copy.copy(h_limit_s))
        self.points = kwargs.get('points', 50)
        self.d_temp_separation_min = kwargs.get('d_temp_separation_min', 0.5)
        self.calc_type = kwargs.get('calc_type', "const")
        self.name = kwargs.get('name', "evaporator")
        self.plot_info = kwargs.get('plot_info', None)
        self.heating = -1
        if h_out_w < state_in_w[2]:
            self.heating = 1
        self.all_states = np.zeros(
            (2, self.points, len(cb.fprop._THERMO_STRING.split(";"))))
        self.h_in_out = np.zeros((2, 4))
        self.dt_mean = None
        self.dt_min = None
        self.dt_max = None
        self.warning = 0
        self.warning_message = "All o.k."

    @classmethod
    def create_from_input(cls, input_hex, temp_ambient, exchanger_name):
        # Find the working fluid and storage fluid details
        working_fluid_info = input_hex.get("working_fluid")
        storage_fluid_info = None

        for key, value in input_hex.items():
            if "storage" in key.lower():
                storage_fluid_info = value
                break

        if not working_fluid_info or not storage_fluid_info:
            raise ValueError("Missing working fluid or storage fluid information in input data.")

        # Initialize fluids
        working_fluid = init_fluid(working_fluid_info)
        storage_fluid = init_fluid(storage_fluid_info)

        # Determine the species mappings for the given exchanger
        species_mapping = input_hex[exchanger_name]["species"]
        working_fluid_states = species_mapping["working_fluid"]
        storage_fluid_states = next(value for key, value in species_mapping.items() if "storage" in key.lower())

        # Extract temperatures and pressures for storage fluid
        
        temp_out_storage = storage_fluid_info[storage_fluid_states["out"]]
        temp_in_storage = storage_fluid_info[storage_fluid_states["in"]]
        if temp_in_storage == "ambient":
            temp_in_storage = temp_ambient
        if temp_out_storage == "ambient":
            temp_out_storage = temp_ambient

        p_low_storage = storage_fluid_info["p_low"]

        # Calculate enthalpies for storage fluid
        
        state_out_storage = storage_fluid.set_state([temp_out_storage, p_low_storage], "TP")
        state_in_storage = storage_fluid.set_state([temp_in_storage, p_low_storage], "TP")

        h_in_storage = state_in_storage[2]
        h_out_storage = state_out_storage[2]

        # Determine direction of heat exchange
        dt_min = input_hex[exchanger_name]["dt_min"]
        temp_in_working = working_fluid_info[working_fluid_states["in"]]
        temp_out_working = working_fluid_info[working_fluid_states["out"]]
        if temp_in_working == "ambient":
            temp_in_working = temp_ambient
        if temp_out_working == "ambient":
            temp_out_working = temp_ambient

        if temp_in_working > temp_in_storage:
            heating = 1  # Evaporator (heating of secondary fluid)
            temp_in_working += dt_min
            temp_out_working += dt_min
        else:
            heating = -1  # Condenser
            temp_in_working -= dt_min
            temp_out_working -= dt_min

        # Calculate enthalpies for working fluid
        p_low_working = working_fluid_info["p_low"]
        state_in_working = working_fluid.set_state([temp_in_working, p_low_working], "TP")
        state_out_working = working_fluid.set_state([temp_out_working, p_low_working], "TP")

        h_in_working = state_in_working[2]
        h_out_working = state_out_working[2]

        # Create StaticHeatExchanger instance
        return cls(
            fluids=[working_fluid, storage_fluid],
            h_dot_min=input_hex[exchanger_name]["q_dot"],
            h_out_w=h_out_working,
            h_limit_s=h_out_storage,
            d_temp_separation_min=dt_min,
            calc_type=input_hex[exchanger_name].get("calc_type", "const"),
            points=input_hex[exchanger_name].get("points", 50),
            name=input_hex[exchanger_name].get("name", exchanger_name),
            plot_info=input_hex[exchanger_name].get("plot_info", None),
        )

# Example usage
temp_ambient = 293.15  # Example ambient temperature in Kelvin
input_hex = {
    'condenser': {
        'model': "StaticHeatExchanger",
        "calc_type": "const",
        "species": {"working_fluid": {"in": "temp_high", "out": "temp_low"},
                    "hot_storage": {"in": "temp_low", "out": "temp_high"}},
        "dt_min": 3.,
        "q_dot": 1000.,
        "overall_u": 100,
        'area': 1,
    },
    'hot_storage': {
        "species": "Water",
        "fractions": [1.0],
        "p_low": 2e5,
        "temp_low": "ambient",
        "temp_high": 360.0,
        'props': "REFPROP",
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
        'props': "REFPROP",
    },
}

heat_exchanger_instance = StaticHeatExchanger.create_from_input(input_hex, temp_ambient, "condenser")
