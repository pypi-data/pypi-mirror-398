# -*- coding: utf-8 -*-
"""
Created on Sun May 21 08:51:33 2023

@author: atakan
"""


import copy
import json
import yaml

# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import minimize, Bounds  # root, root_scalar
import matplotlib.pyplot as plt
import carbatpy as cb


class StaticHeatExchanger:
    """
    Class for static counter-flow heat exchanger

    means: no time dependence and no heat transfer coefficients * areas
    are used (UA)! Instead a minimum approach temperature is tried to be met.
    At the moment, this is mainly done by varying one of the mass flow rates.
    But this is sometimes not enough and a variation of the working fluid
    pressure will soon be included.
    Only the first law and second law will be checked (the latter must be
    improved).

    """

    def __init__(self, fluids, h_dot_min, h_out_w, h_limit_s,
                 **kwargs):  # points=50, d_temp_separation_min=0.5, calc_type="const",name="evaporator"):
        """
        class to calculate (static/steady state) heat-exchangers

        includes pinch-point analysis and plotting,
        only implemented for simple thermodynamic calculations
        (no convection coefficients and heat exchanger areas regarded yet)

        Parameters
        ----------
        fluids : list of 2 fprop.Fluid
            The definition of the two fluids, as they enter the heat exchangers.
            Typically at room temperature.
        h_dot_min : float
            enthalpy flow rate (W) which has to be transfered.
        h_out_w : float
            exit enthalpy of the working fluid.
        h_limit_s : float,
            if there is a limit in enthalpy for the secondary fluid, it can be
            given here. It is also a starting value for possible iterations.
        kwargs : dict, optional
            Optional parameters for the heat exchanger configuration:

                - points : int, for how many points (array) shall the minimum approach temperature
                    be checked and properties be returned (for plotting etc.). default 50
                - d_temp_separation_min : float, Minimium approach temperature (
                    pinch point) between the two fluids. default 0.5
                - calc_type : str, which calculation type shall be performed; only one implemented so
                    far, default "const"
                - name : str, name of the heat exchanger .default "evaporator"
                - plot_info : dict, if not None, a Figure, an Axes, a list of What shall be plotted,
                    a list with the colour/styles and a list with the labels must be
                    passed. in "what", the two numbers coincide with the fluid THERMO
                    order. The x-shift can be used in cycle calculations, to shift the
                    curves, by the value (it will be added).
                    The names in the dictionary are: "fig", "ax", "what","col",
                    "label", "x-shift". Default is empty.default {}


        Returns
        -------
        None.

        """
        self.fluids = fluids
        state_in_w = fluids[0].properties.state
        self.m_dot_s = 0
        self.h_limit_s = h_limit_s
        self.q_dot = h_dot_min
        self.m_dot_w = np.abs(h_dot_min/(h_out_w-state_in_w[2]))
        self.h_out_w = h_out_w
        self.h_out_s = float(copy.copy(h_limit_s))  # this may be varied
        self.points = kwargs.get('points', 50)
        self.d_temp_separation_min = kwargs.get('d_temp_separation_min', 0.5)
        self.calc_type = kwargs.get('calc_type', "const")
        self.name = kwargs.get('name', "evaporator")
        self.plot_info = kwargs.get('plot_info', None)
        # self.points = points
        # self. d_temp_separation_min = d_temp_separation_min
        self.heating = -1
        if h_out_w < state_in_w[2]:
            self.heating = 1  # condenser (heating of the secondary fluid)
        # self.calc_type = calc_type
        # self.name = name
        self.all_states = np.zeros(
            (2, self.points, len(cb.fprop._THERMO_STRING.split(";"))))
        self.h_in_out = np.zeros((2, 4))
        self.dt_mean = None
        self.dt_min = None
        self.dt_max = None
        self.warning = 0
        self.warning_message = "All o.k."
        

    @property
    def plot_info(self):
        return self._plot_info

    @plot_info.setter
    def plot_info(self, value):
        if value is None:
            value = {}
        elif not isinstance(value, dict):
            raise ValueError("plot_info must be a dictionary")
        self._plot_info = value
        
    @property
    def all(self):
        # Erstelle ein Dictionary aller Attribute außer self.all
        return {key: value for key, value in self.__dict__.items() if key != 'all'}

    def to_dict(self):
        # Alle Attribute extrahieren, keine Methoden und self.all ausschließen
        result = {}
        for key, value in self.__dict__.items():
            if key != 'all':  # Beispiel für ein zu ignorierendes Attribut
                if isinstance(value, np.ndarray):
                    result[key] = value.tolist()  # NumPy-Arrays in Listen konvertieren
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()  # Konvertieren, wenn `to_dict` vorhanden
                else:
                    result[key] = value
        return result

    @classmethod
    def from_dict_old(cls, data):
        instance = cls.__new__(cls)
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
                # Annahme: Listen sind NumPy-Arrays
                setattr(instance, key, np.array(value))
            elif isinstance(value, dict) and 'value' in value:
                # Annahme: Dictionary ist eine Instanz von AnotherClass
                #setattr(instance, key, AnotherClass.from_dict(value))
                pass
            else:
                setattr(instance, key, value)
        return instance

    def save_to_file(self, file_path):
        try:
            data = self.to_dict()
            if file_path.endswith('.json'):
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'w') as file:
                    yaml.dump(data, file)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml/.yml")
        except Exception as e:
            print(f"Error saving to file: {e}")

    @classmethod
    def load_from_file(cls, file_path):
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as file:
                    data = json.load(file)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'r') as file:
                    data = yaml.load(file, Loader=yaml.SafeLoader)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml/.yml")

            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading from file: {e}")
            return None
        
    @classmethod
    def from_dict(cls, input_hex, exchanger_name="condenser", temp_ambient=None, **kwargs ):
        # Find the working fluid and storage fluid details
        if not temp_ambient:
            temp_ambient =cb.CB_DEFAULTS["General"]["T_SUR"]
            
        working_fluid_info = input_hex.get("working_fluid")
        storage_fluid_info = None
    
        for key, value in input_hex.items():
            if "storage" in key.lower():
                storage_fluid_info = value
                break
    
        if not working_fluid_info or not storage_fluid_info:
            raise ValueError("Missing working fluid or storage fluid information in input data.")
    
        # Initialize fluids
        working_fluid = cb.init_fluid(working_fluid_info["species"],
                                      working_fluid_info["fractions"],
                                      props=working_fluid_info["props"]
                                      )
        storage_fluid = cb.init_fluid(storage_fluid_info["species"],
                                      storage_fluid_info["fractions"],
                                      props=storage_fluid_info["props"])
    
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
        
        state_out_working = working_fluid.set_state([temp_out_working, p_low_working], "TP")
        state_in_working = working_fluid.set_state([temp_in_working, p_low_working], "TP")
    
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

    def pinch_calc(self,  verbose=False):
        """
        Calculate the changes in enthalpy and temperature in the heat exchanger

        counter-flow hex assumed! Both flows are isobaric.
        Is used to check, whether the second law is violated. The factor can
        be used to vary the mass flow rate of the working fluid, until no
        violation is found (done in root finding).

        Parameters
        ----------
        verbose : boolean, optional
            if True, several variables will be printed out. Default is False.



        Raises
        ------
        Exception
            if temperatures are not consistent.

        Returns
        -------
        m_dot_s : float
            secondary fluid mass flow rate (kg/s.
        d_tempall : numpy-array
            The temperature differences along the counter-flow heat exchanger.
        w_array : array
            properties of the working fluid along the heat exchanger
            (T,p,h, etc. see fluid class).
        s_array : array
            properties of the secondary fluid along the heat exchanger
            (T,p,h, etc. see fluid class).

        """
        self.warning = 0
        self.warning_message = "All o.k."
        w_in = copy.copy(self.fluids[0])
        s_in = copy.copy(self.fluids[1])

        w_out = copy.copy(self.fluids[0])  # not yet the correct state!
        s_out = copy.copy(self.fluids[1])

        #  fixed values
        self. h_in_out[1, 0] = s_in.properties.enthalpy
        self. h_in_out[0, 0] = w_in.properties.enthalpy
        self. h_in_out[0, 1] = self.h_out_w

        # fixed limiting state, secondary fluid
        state_out_s = s_out.set_state([self.h_out_s,
                                       s_in.properties.pressure], "HP")

        self. h_in_out[1, 1] = state_out_s[2]

        h_delta_s = np.abs(
            state_out_s[2] - s_in.properties.enthalpy)

        # fixed heat flow,  determines mass flow rate
        self.m_dot_s = self.q_dot / h_delta_s

        s_array = self._calculate_state_array(s_out, self.h_in_out[1, :2])
        w_array = self._calculate_state_array(w_out, self.h_in_out[0, 1::-1])
        # temperature difference, ok?

        d_tempall = w_array[:, 0]-s_array[:, 0]

        self.dt_mean, self.dt_min, self.dt_max = d_tempall.mean(), np.abs(
            d_tempall).min(), np.abs(d_tempall).max()

        self._check_temperature_consistency(d_tempall)

        if self.plot_info:
            self._plot_heat_exchanger(w_array, s_array)

        if verbose:
            self._print_verbose(d_tempall)
        self.all_states[0,:,:] = w_array
        self.all_states[1,:,:] = s_array
        return self.m_dot_s, d_tempall*self.heating, w_array, s_array

    def _pinch_root(self, h_out_s,  secondary, verbose=False):
        """
        Function for finding the minimum mean temperature difference in a heat
        exchanger, while not going below the minimum approach temperature.

        The output enthalpy of the secondary fluid is set (as default) and the
        heat exchanger is evaluated.


        Parameters
        ----------
        h_out_s : float
            the output enthalpy, default would be of the secondary fluid.
        secondary : boolean
            shall the secondary fluid output be varied (or the working fluid)?

        Returns
        -------
        mean T-difference, float
            root tries to reach a value of 0.

        """

        if isinstance(h_out_s, float):  # numpy expects a float (later)
            value = h_out_s
        else:
            value = h_out_s[0]

        if secondary:
            self.h_out_s = value
        else:
            self.h_out_w = value

        mdot_s, d_temps, wf_states, sf_states = self.pinch_calc()

        if self.warning < 100:
            return abs(self.dt_mean)
        return 500.0
    
    def _p_opti_help(self, values, secondary=True, verbose=False, **kwargs):
        what =kwargs.get("what","TP")
        pressure_w, h_out = values
        name_o = what.replace("P","")
        if verbose:
            print("p_opti:", values, name_o,self.dt_mean)
        if name_o == "T":
            other =self.fluids[0].val_dict["Temperature"]
        else:
            raise NotImplementedError(f"pressure optimization not implemnted for {name_o}")
        
        state_in = self.fluids[0].set_state([pressure_w, other], what)
        self.find_pinch(secondary)
        if verbose:
            print("p_opti:", values, name_o,self.dt_mean)
        if self.warning ==0:
            return self.dt_mean
        return 999.0
    
    def opti_hex_p_pinch(self, secondary=True):
        """
        Function tries to vary the workin fluid pressure  until a
        minimum approach temperature is reached. This also changes the
        mass flow rate.  This is then also the new
        exit state
        within the heat exchanger. If this is also not succesful,
        self.warning is set to 1. This should be checked.
        Parameters
        ----------
        secondary : Boolean, optional
            shall the output state of the secondary (True) or the working
            (False) fluid be varied? default = True

        Returns
        -------
        float
            the optimized enthalpy of the secondary fluid.

        """
        verbose = False
        h0 = copy.copy(self.h_out_s if secondary else self.h_out_w)
        p0 = self.fluids[0].val_dict["Pressure"] # for testing
        bound = Bounds(lb=[p0*.9, h0*.99], ub=[p0*1.1,h0*1.01])
        # if secondary:
        #     x0 = copy.copy(self.h_out_s)
        # else:
        #     x0 = copy.copy(self.h_out_w)
        initial =np.array([p0, h0])

        tolerance = 1e-3

        try:

            result = minimize(self._p_opti_help, initial, args=(secondary, True),
                              method='Nelder-Mead', tol=tolerance, bounds=bound)

            if verbose:
                print(
                    f"result {result}, heating {self.heating}")

            if result.success or result.status == 2:
                if result.status == 2:
                    self.warning = 2  # T-difference probably smaller
                    self.warning_message = "Minimization problem: "+result.message
                if secondary:
                    self.h_out_s = result.x[0]
                else:
                    self.h_out_w = result.x[0]
                print(
                    f"Min T-distance {self.dt_min:.3f}, Mean T-distance {self.dt_mean:.3f}")

                return result.x[0]

        # except:
        except Exception as e:
            self._handle_exception(e)
            return 10000
        print("root-finding problem! (in heat_exchanger_thermo_v2.find_pinch)",
              result)
        print(f"Heating: {self.heating}")
        self.warning = 1
        return self.warning            

    def find_pinch(self, secondary=True, verbose = False):
        """
        Function tries to vary the secondary fluid enthalpy  until a
        minimum approach temperature is reached. This also changes the
        mass flow rate.  This is then also the new
        exit state
        within the heat exchanger. If this is also not succesful,
        self.warning is set to 1. This should be checked.
        Parameters
        ----------
        secondary : Boolean, optional
            shall the output state of the secondary (True) or the working
            (False) fluid be varied? default = True

        Returns
        -------
        float
            the optimized enthalpy of the secondary fluid.

        """
        
        x0 = copy.copy(self.h_out_s if secondary else self.h_out_w)
        # if secondary:
        #     x0 = copy.copy(self.h_out_s)
        # else:
        #     x0 = copy.copy(self.h_out_w)

        tolerance = 1e-3

        try:

            result = minimize(self._pinch_root, x0, args=(secondary,),
                              method='Nelder-Mead', tol=tolerance)

            if verbose:
                print(
                    f"result {result}, heating {self.heating}")

            if result.success or result.status == 2:
                if result.status == 2:
                    self.warning = 2  # T-difference probably smaller
                    self.warning_message = "Minimization problem: "+result.message
                if secondary:
                    self.h_out_s = result.x[0]
                else:
                    self.h_out_w = result.x[0]
                if verbose:
                    print(f"Min T-distance {self.dt_min:.3f}, Mean T-distance {self.dt_mean:.3f}")

                return result.x[0]

        # except:
        except Exception as e:
            self._handle_exception(e)
            return 10000
        print("root-finding problem! (in heat_exchanger_thermo_v2.find_pinch)",
              result)
        print(f"Heating: {self.heating}")
        self.warning = 1
        return self.warning

    def pinch_plot(self, plot_fname="", plotting=True, **kwargs):
        """
        calculates the secondary fluid output state and mass flow, for the
        minimum approach temperature of the HeatExchanger instance. When wanted,
        this is also plotted

        Parameters
        ----------
        plot_fname : string, optional
            file-name to store the plot. The default is "".
        plotting : Boolean, optional
            should it be plotted? The default is True.

        Returns
        -------
        m_dot_s : float
            mass flow raete of the secondary fluid in SI units (kg/s).
        d_tempall : np.array
            the temperature differences between the two fluids along the heat
            exchanger.
        w_array : np.array [self.points, 7]
            the states of the working fluid along the heat exchanger.
        s_array : np.array [self.points, 7]
            the states of the secondary fluid along the heat exchanger.

        """
        verbose =kwargs.get("verbose",False)
        if verbose:
            print(f"------pinch-plot running -----plot:{plotting}")
        m_dot_s, d_tempall, w_array, s_array = self.pinch_calc()

        if plotting:
            h_w_plot_array = (
                w_array[:, 2] - w_array[:, 2].min()) * self.m_dot_w
            fig, ax_one = plt.subplots(1, 1)
            ax_one.plot((s_array[:, 2] - s_array[:, 2].min()) * self.m_dot_s,
                        s_array[:, 0], "v")
            ax_one.plot(h_w_plot_array, w_array[:, 0], "o")
            ax_one.set_xlabel(
                "specific enthalpy flow per mass of secondary fluid / (J / kg)")
            ax_one.set_ylabel("temperature / (K)")
            ax_one.set_title("heat exchanger, simple")
        if plot_fname != "":
            fig.savefig(plot_fname)

        return m_dot_s, d_tempall, w_array, s_array

    def _calculate_state_array(self, fluid, h_range):

        h_array = np.linspace(h_range[0], h_range[1], self.points)
        values = np.zeros((self.points, 2))
        values[:, 0] = h_array
        values[:, 1] = fluid.properties.pressure
        return fluid.set_state_v(values, "HP")

    def _check_temperature_consistency(self, d_tempall):
        eps_min = -1e-3
        positive = np.any(d_tempall > 0)
        negative = np.any(d_tempall < 0)
        below = True
        if self.heating < 0:
            below = False
        crossing = (positive > 0 and negative > 0)
        wrong_side = (positive > 0 and not below) or (negative > 0 and below)
        abs_dt_min = np.abs(self.dt_min)
        difference = abs_dt_min - self.d_temp_separation_min
        # print(f"Debug: abs_dt_min = {abs_dt_min}, d_temp_separation_min = {self.d_temp_separation_min}, difference = {difference}")

        if difference < eps_min:
            self.warning = 907
            self.warning_message = "Below minimum approach temperature!"
            # print(f"907: {difference}, {abs_dt_min}, {self.d_temp_separation_min}")

        elif crossing or wrong_side:
            self.warning = 999
            self.dt_mean = 1e6
            self.warning_message = "Temperatures crossing or wrong side!"
        else:
            self.warning = 0
            self.warning_message = "All o.k."

    def _plot_heat_exchanger(self, w_array, s_array):
        plot_info = self.plot_info
        # print("Plot info:", plot_info)  # Debugging-Ausgabe
        if plot_info["what"][0] == 2:
            data_w = (w_array[:, plot_info["what"][0]] - w_array[:,
                      plot_info["what"][0]].min()) * self.m_dot_w + plot_info["x-shift"][0]
            data_s = (s_array[:, plot_info["what"][0]] - s_array[:,
                      plot_info["what"][0]].min()) * self.m_dot_s + plot_info["x-shift"][1]
            plot_info["ax"].plot(data_w, w_array[:, plot_info["what"][1]],
                                 plot_info["col"][0], label=plot_info["label"][0])
            plot_info["ax"].plot(data_s, s_array[:, plot_info["what"][1]],
                                 plot_info["col"][1], label=plot_info["label"][1])
        else:
            print(
                f"H-Ex: plotting only implemented for T-H_dot [2,0]. You requested {plot_info['what']}")

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


if __name__ == "__main__":
    # two test cases condenser and evaporator:

    FLUID = "Propane * Pentane"  # working fluid
    FLS = "Methanol"  # "Water"  # secondary fluid
    comp = [.50, 0.5]
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)

    secFlm = cb.fprop.FluidModel(FLS)
    secFluid = cb.fprop.Fluid(secFlm, [1.])
    D_TEMP_MIN = 5.0

    # Condenser, working fluid fixes all, secondary output enthalpy can be varied:
    SEC_TEMP_IN = 300.0
    SEC_TEMP_OUT_MAX = 370.0
    SEC_PRES_IN = 5e5
    H_DOT = 1e3
    state_sec_out = secFluid.set_state([SEC_TEMP_OUT_MAX, SEC_PRES_IN], "TP")

    state_sec_in = secFluid.set_state(
        [SEC_TEMP_IN, SEC_PRES_IN], "TP")  # this is the entering state

    # working fluid

    TEMP_SAT_VAP = SEC_TEMP_OUT_MAX + D_TEMP_MIN
    state_in = myFluid.set_state(
        [TEMP_SAT_VAP, 1.], "TQ")  # find minimum pressure

    WF_TEMP_IN = TEMP_SAT_VAP + D_TEMP_MIN
    WF_TEMP_OUT = SEC_TEMP_IN + D_TEMP_MIN
    state_out = myFluid.set_state([WF_TEMP_OUT, state_in[1]], "TP")
    
    # now plotting can directly be done in pinch_calc 2024-05-24
    fig_act, ax_act = plt.subplots(1)
    PLOT_INFO = {"fig": fig_act, "ax": ax_act, "what": [2, 0], "col": ["r:", "ko"],
                 "label": ["work,c", "sec,c"], "x-shift": [0, 0]}
    
    # a simple way to find an optimal/better pressure level
    pressures_good =[]
    p_start = state_out[1]
    
    p_range = np.linspace(p_start*.87, p_start*1.015,3)
    for p_act in p_range:

        state_in = myFluid.set_state([p_act,
                                      WF_TEMP_IN],
                                     "PT")
        # myFluid.print_state()
    
        hex0 = StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
                                   state_sec_out[2],
                                   d_temp_separation_min=D_TEMP_MIN)
        
    
        factor0 = hex0.find_pinch()
        if hex0.warning ==0:
            pressures_good.append([p_act, hex0.dt_mean, hex0.warning, hex0.warning_message])
        print(f"{p_act/1e5:.2f} bar", hex0.dt_mean, hex0.warning, hex0.warning_message)
    if hex0.warning > 0:
        print(hex0.warning_message)
    print("useful pressures:\n",pressures_good,"\n\n")    
    # # pressure optimization 2024-07-22
    # p_opt =hex0.opti_hex_p_pinch()
    # print(f"Optimal pressure {p_opt}, Warning: {hex0.warning_message}")

    hex0.plot_info = PLOT_INFO
    hex0.plot_info = PLOT_INFO
    hex0.pinch_calc(verbose=True)
    ax_act.legend()
    # -----------------------------------------------
    #       Previous way
    # ms0, d_tempall0, w0, s0 = hex0.pinch_plot("hex-plot.png")

    #  Evaporator: ----------------------------

    SEC_TEMP_IN = 300.0
    SEC_TEMP_OUT = 285
    SEC_PRES_IN = 15e5
    H_DOT = 1e3
    extra = 2
    # D_TEMP_SUPER = 5.
    D_TEMP_MIN = 6.0
    state_sec_out = secFluid.set_state([SEC_TEMP_OUT, SEC_PRES_IN], "TP")
    # this mus be the last set_state before the hex is constructed:
    state_sec_in = secFluid.set_state([SEC_TEMP_IN, SEC_PRES_IN], "TP")

    # WF_TEMP_IN = SEC_TEMP_OUT  # - D_TEMP_MIN
    state_out = myFluid.set_state([SEC_TEMP_IN-D_TEMP_MIN - extra, 1.0], "TQ")
    state_in = myFluid.set_state(
        [SEC_TEMP_OUT-D_TEMP_MIN - extra, state_out[1]], "TP")

    # print("state in", state_in)

    hex1 = StaticHeatExchanger([myFluid, secFluid], H_DOT, state_out[2],
                               state_sec_out[2],
                               d_temp_separation_min=D_TEMP_MIN)
    # ms1, d_tempall1, w1, s1 = hex1.pinch_calc()

    factor_out = hex1.find_pinch()
    if hex1.warning > 2:
        print("Second heat exchanger:", hex1.warning_message, hex1.dt_min)
    else:

        # plotting in the same figure
        PLOT_INFO = {"fig": fig_act, "ax": ax_act, "what": [2, 0], "col": ["k:", "bo"],
                     "label": ["work,e", "sec,e"], "x-shift": [0, 0]}
        hex1.plot_info = PLOT_INFO
        hex1.pinch_calc(verbose=True)
        ax_act.legend()
    
    #----------------------------------
    # create from dictionary
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

    heat_exchanger_instance = StaticHeatExchanger.from_dict(input_hex)
