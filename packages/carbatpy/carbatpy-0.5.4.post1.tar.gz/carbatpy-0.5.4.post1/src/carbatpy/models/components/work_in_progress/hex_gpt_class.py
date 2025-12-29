# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 17:36:05 2024

@author: atakan
"""

import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable, DataAll, DataNode
import json
import yaml
import numpy as np
import matplotlib.pyplot as plt
import copy
from scipy.optimize import minimize


class HeatExchangerBase(Serializable):
    """Base class for heat exchangers.

    All inputs come either from a file (json/yaml) or from a dictionary.

    """

    def __init__(self, inputs, name=None, **kwargs):
        """
        Set the heat exchanger input parameters.

        Parameters
        ----------
        inputs : string or dict
            If string, it must be a valid filename (json or yaml) with the dictionary content.
        name : string, optional
            The name of the heat exchanger. The default is None.
        **kwargs : dict
            - plot_info : dict, a dictionary with file, axes (from matplotlib), labels, symbols
              used for plotting (as defined in self.plot()).

        Raises
        ------
        NotImplementedError
            If the inputs are not correctly provided.

        """
        self.name = name if name else "heat-exchanger"
        self.plot_info = kwargs.get("plot_info", None)
        self.output = Serializable()
        self.all_states = {}
        self.warning = DataAll(value=0, message="All o.k.")
        self._defaults = DataAll()

        # Load inputs from a file or directly from a dictionary
        print("hier", isinstance(inputs, dict), inputs, name)
        if isinstance(inputs, dict):
            self.inputs = inputs
            print("hier")
        elif isinstance(inputs, str):
            try:
                with open(inputs, "r") as file:
                    if "json" in inputs:
                        self.inputs = json.load(file)
                    elif "yaml" in inputs:
                        self.inputs = yaml.safe_load(file)
                    else:
                        raise ValueError("Unsupported file format.")
            except Exception as e:
                print(f"Error loading input file: {e}")
                raise
        else:
            raise NotImplementedError(
                f"Unsupported input type: {type(inputs)}, {inputs}"
            )

        self._inp = DataAll(**self.inputs)

        match self.inputs[self.name]["model"]:  # noqa
            case "StaticHeatExchanger":
                pass
            case _:
                raise NotImplementedError(
                    f"This heat exchanger type is not implemented: {self._inp.process[self.name]}")

    def calc(self, **kwargs):
        """Selects the calculation method and calls the appropriate function."""
        raise NotImplementedError("This method must be overridden in subclasses.")

    def plot(self, **kwargs):
        """Plot the results into a given or a new figure."""
        raise NotImplementedError("This method must be overridden in subclasses.")

    def save(self, filename, **kwargs):
        """Save all results into one or several files."""
        raise NotImplementedError("This method must be overridden in subclasses.")

    def _costs(self, filename, **kwargs):
        """Calculate costs via calc()."""
        raise NotImplementedError("This method must be overridden in subclasses.")


class StaticHeatExchanger(HeatExchangerBase):
    """Class for static counter-flow heat exchanger.

    No time dependence and no heat transfer coefficients * areas are used (UA)!
    Instead, a minimum approach temperature is tried to be met.
    """

    # fluids, h_dot_min, h_out_w, h_limit_s, **kwargs):
    def __init__(self, inputs, name=None, **kwargs):
        """
        Initialize a static heat exchanger for steady-state calculations.

        Parameters
        ----------
        fluids : list of cb.fprop.Fluid
            The definition of the two fluids, as they enter the heat exchangers.
        h_dot_min : float
            Enthalpy flow rate (W) which has to be transferred.
        h_out_w : float
            Exit enthalpy of the working fluid.
        h_limit_s : float
            Limit in enthalpy for the secondary fluid.
        kwargs : dict, optional
            Optional parameters for the heat exchanger configuration.
        """
        super().__init__(inputs, name, **kwargs)
        fluids, h_dot_min, h_out_w, h_limit_s, d_temp_separation = from_dict(inputs, name, kwargs)
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
        self.heating = 1 if h_out_w < state_in_w[2] else -1
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
        return {key: value for key, value in self.__dict__.items() if key != 'all'}

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if key != 'all':
                if isinstance(value, np.ndarray):
                    result[key] = value.tolist()
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        return result

    
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
    def _handle_exception(self, e):
        print("find pinch:", type(e))
        print(e.args)
        print(e)
        print("root-exception", self.heating)
        
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

    # def calculate_pinch_point(self, verbose=False):
    #     """Calculate pinch point and all other states for both fluids."""

    #     from scipy.optimize import fsolve

    #     results = self.all_states.copy()
    #     # initial guess
    #     if verbose:
    #         print("Guessing the enthalpy outlet for the secondary fluid")
    #     x0 = self.h_out_s
    #     if not x0:
    #         x0 = self.h_limit_s

    #     def _res_func(h_out_s):
    #         return self.find_pinch_root(h_out_s, verbose=verbose)[0, -1, 2] - self.h_limit_s

    #     self.h_out_s = fsolve(_res_func, x0)[0]
    #     if verbose:
    #         print(f"solved h_out_s = {self.h_out_s}")
    #     # set all states:
    #     self.all_states = self.find_pinch_root(self.h_out_s, verbose=verbose)

    # def find_optimal_pinch(self, secondary=True, verbose=False):
    #     """Find the optimal pinch point for the heat exchanger.

    #     Parameters
    #     ----------
    #     secondary : bool, optional
    #         If True, the optimization is for the secondary fluid. The default is True.
    #     verbose : bool, optional
    #         If True, additional information is printed. The default is False.

    #     Returns
    #     -------
    #     None.
    #     """
    #     from scipy.optimize import minimize

    #     # Define the objective function
    #     def objective(enthalpy_out):
    #         return np.abs(
    #             self.find_pinch_root(enthalpy_out, secondary, verbose)[0, -1, 2]
    #             - self.h_limit_s
    #         )

    #     # Initial guess for the outlet enthalpy
    #     initial_guess = self.h_out_s if secondary else self.h_out_w

    #     # Perform the optimization
    #     result = minimize(objective, initial_guess, method='Nelder-Mead')
    #     optimal_enthalpy_out = result.x[0]

    #     if secondary:
    #         self.h_out_s = optimal_enthalpy_out
    #     else:
    #         self.h_out_w = optimal_enthalpy_out

    #     self.calculate_pinch_point(verbose)

    # def optimize_pressure(self, values, secondary=True, verbose=False, **kwargs):
    #     """
    #     Optimizes the pressures and the mass flows of both fluids.

    #     Parameters
    #     ----------
    #     values : list or ndarray
    #         The values which have to be optimized.
    #     secondary : bool, optional
    #         True (default) means the secondary (storage) fluid.
    #     verbose : bool, optional
    #         Print optimization progress and result.

    #     Raises
    #     ------
    #     ValueError
    #         If the optimization does not converge.

    #     Returns
    #     -------
    #     None.

    #     """
    #     res = self.find_pinch_root(self.h_out_s, secondary, verbose)
    #     t_pinch = res[0, -1, 0]
    #     p_pinch = res[0, -1, 1]
    #     h_pinch = res[0, -1, 2]
    #     if not secondary:
    #         return t_pinch, p_pinch, h_pinch
    #     return p_pinch

    # def plot_pinch_point(self, plot_fname="", plotting=True, **kwargs):
    #     """Plot the pinch point information."""
    #     import matplotlib.pyplot as plt

    #     # Setting up plot details
    #     title = kwargs.get("title", "Pinch Point Plot")
    #     xlabel = kwargs.get("xlabel", "Enthalpy [kJ/kg]")
    #     ylabel = kwargs.get("ylabel", "Temperature [°C]")
    #     legend_loc = kwargs.get("legend_loc", "best")

    #     # Extracting necessary data
    #     working_fluid_data = self.all_states[0]
    #     storage_fluid_data = self.all_states[1]

    #     # Plotting
    #     plt.figure(figsize=(10, 6))
    #     plt.plot(
    #         working_fluid_data[:, 2],  # Enthalpy (h)
    #         working_fluid_data[:, 0],  # Temperature (T)
    #         label="Working Fluid",
    #         color="blue",
    #     )
    #     plt.plot(
    #         storage_fluid_data[:, 2],
    #         storage_fluid_data[:, 0],
    #         label="Storage Fluid",
    #         color="red",
    #     )

    #     # Adding plot details
    #     plt.title(title)
    #     plt.xlabel(xlabel)
    #     plt.ylabel(ylabel)
    #     plt.legend(loc=legend_loc)

    #     # Saving or showing the plot
    #     if plotting:
    #         plt.show()
    #     if plot_fname:
    #         plt.savefig(plot_fname)
    
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

    def save_configuration_to_file(self, file_path):
        """Save the heat exchanger configuration to a file."""
        config_data = self.to_dict()
        with open(file_path, "w") as file:
            if file_path.endswith(".json"):
                json.dump(config_data, file, indent=4)
            elif file_path.endswith(".yaml"):
                yaml.dump(config_data, file)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml")

    @staticmethod
    def load_configuration_from_file(file_path):
        """Load a heat exchanger configuration from a file."""
        with open(file_path, "r") as file:
            if file_path.endswith(".json"):
                config_data = json.load(file)
            elif file_path.endswith(".yaml"):
                config_data = yaml.safe_load(file)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml")
        return config_data

    def calc(self, **kwargs):
        """Override calc method for specific calculation logic."""
        self.pinch_calc(verbose=kwargs.get("verbose", False))

    def plot(self, **kwargs):
        """Override plot method for specific plotting logic."""
        self.plot_pinch_point(plot_fname=kwargs.get(
            "plot_fname", ""), plotting=True, **kwargs)

    def save(self, filename, **kwargs):
        """Override save method for specific saving logic."""
        self.save_configuration_to_file(filename)

    def _costs(self, filename, **kwargs):
        """Override _costs method for specific cost calculation."""
        pass

def from_dict(input_hex, exchanger_name="condenser", temp_ambient=None, **kwargs):
    if not temp_ambient:
        temp_ambient = cb.CB_DEFAULTS["General"]["T_SUR"]

    working_fluid_info = input_hex.get("working_fluid")
    storage_fluid_info = None

    for key, value in input_hex.items():
        if "storage" in key.lower():
            storage_fluid_info = value
            break

    if not working_fluid_info or not storage_fluid_info:
        raise ValueError(
            "Missing working fluid or storage fluid information in input data.")

    working_fluid = cb.init_fluid(working_fluid_info["species"],
                                  working_fluid_info["fractions"],
                                  props=working_fluid_info["props"])
    storage_fluid = cb.init_fluid(storage_fluid_info["species"],
                                  storage_fluid_info["fractions"],
                                  props=storage_fluid_info["props"])

    species_mapping = input_hex[exchanger_name]["species"]
    working_fluid_states = species_mapping["working_fluid"]
    storage_fluid_states = next(
        value for key, value in species_mapping.items() if "storage" in key.lower())

    temp_out_storage = storage_fluid_info[storage_fluid_states["out"]]
    temp_in_storage = storage_fluid_info[storage_fluid_states["in"]]
    if temp_in_storage == "ambient":
        temp_in_storage = temp_ambient
    if temp_out_storage == "ambient":
        temp_out_storage = temp_ambient

    p_low_storage = storage_fluid_info["p_low"]

    state_out_storage = storage_fluid.set_state(
        [temp_out_storage, p_low_storage], "TP")
    state_in_storage = storage_fluid.set_state([temp_in_storage, p_low_storage], "TP")

    h_in_storage = state_in_storage[2]
    h_out_storage = state_out_storage[2]

    dt_min = input_hex[exchanger_name]["dt_min"]
    temp_in_working = working_fluid_info[working_fluid_states["in"]]
    temp_out_working = working_fluid_info[working_fluid_states["out"]]
    if temp_in_working == "ambient":
        temp_in_working = temp_ambient
    if temp_out_working == "ambient":
        temp_out_working = temp_ambient

    if temp_in_working > temp_in_storage:
        heating = 1
        temp_in_working += dt_min
        temp_out_working += dt_min
    else:
        heating = -1
        temp_in_working -= dt_min
        temp_out_working -= dt_min

    p_low_working = working_fluid_info["p_low"]

    state_out_working = working_fluid.set_state(
        [temp_out_working, p_low_working], "TP")
    state_in_working = working_fluid.set_state([temp_in_working, p_low_working], "TP")

    h_in_working = state_in_working[2]
    h_out_working = state_out_working[2]

    return [working_fluid, storage_fluid], input_hex[exchanger_name]["q_dot"],\
        h_out_working, h_out_storage, dt_min,\
        # input_hex[exchanger_name].get("calc_type", "const"),\
        # input_hex[exchanger_name].get("points", 50),\
        # exchanger_name,\
        # kwargs
        
        
if __name__ == "__main__":
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
            "temp_high": 370.0,
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
            "temp_high": 420.0,
            "p_low": 1.128250708e+05,
            "p_high": 1.37548728e+06,
            "optimize": "None",
            "setting": "initial",
            'props': "REFPROP",
        },
    }

    heat_exchanger_instance = StaticHeatExchanger(
        input_hex,  "condenser")
    heat_exchanger_instance.calc()
    heat_exchanger_instance.pinch_plot()
    if heat_exchanger_instance.warning:
        print(heat_exchanger_instance.warning_message)
