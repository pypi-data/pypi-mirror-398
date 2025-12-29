# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 08:40:39 2024

@author: atakan
"""
import json
import warnings
import yaml
import pandas as pd

import carbatpy as cb
from carbatpy.helpers.ser_dict import Serializable, DataAll, DataNode


class HeatExc:  # (Serializable):
    """ Base class for heat exchangers.
    
    All inputs come either from a file (json/yaml) or from a dictionary.
    
    """
    
    def __init__(self,  inputs, name=None, **kwargs):
        """
        Set the heat exchanger input parameters.

        Parameters
        ----------
        inputs : string or dictionary
            if string, it must be a valid filename (json or yaml) with the dictionary
            content. In 
        name : string, optional
            the name of the heat exchanger, the program will search for this key it in the
            inputs. The default is None.
        **kwargs : dictionary
            - plot_info : a dictionary with file, axes (from matplotlib), labels, symbols
              used for plotting (as defined in self.plot())
            DESCRIPTION.

        Raises
        ------
        NotImplementedError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if not name:
            name = "heat-exchanger"
        self.plot_info = kwargs.get("plot_info", None)
        self.output = Serializable()
        self.all_states = {}
        self.name = name
        self.warning = DataAll(value=0, message="All o.k.")
        self._defaults = DataAll()
       

        if isinstance(inputs, (dict)):
            self.inputs = inputs
        elif isinstance(inputs, (str)):
            try:
                with open(inputs, "r") as file:
                    if "json" in inputs:
                        self.inputs = json.load(file)
                    elif "yaml" in inputs:
                        self.inputs = yaml.safe_load(file)
            except Exception as e:
                print(f"Problem in heat_ex: {e}")
        else:
            raise NotImplementedError(
                f"Heat exchanger Inputs are not installed for {type(inputs), inputs}!")
        self._inp = DataAll(**self.inputs)
        
        match self._inp.process[self.name]: #noqa
            case "StaticHeatExchanger":
                pass
            case _:
                raise NotImplementedError(f"This heat exchnager is not implemented yet: {self._inp.process[self.name]}")
        
        

    def calc(self, **kwargs):
        """
        Selects the calculation method and calls the appropriate function.
        
        Depending on self.inputs.model
        """
        
                
        raise NotImplementedError("This method must be overridden in subclasses.")
        
    def plot(self, **kwargs):
        """ Plot the results into a given or a new figure.
        Dependes on self.plot_info
        """
        raise NotImplementedError("This method must be overridden in subclasses.")
        
    def save(self, filename, **kwargs):
        """Save all results into one or several files."""
        raise NotImplementedError("This method must be overridden in subclasses.")
        
    def _costs(self, filename, **kwargs):
        """ Costs are calculated via calc()."""
        raise NotImplementedError("This method must be overridden in subclasses.")


if __name__ == "__main__":

    inp = r"C:/Users/atakan/sciebo/results/test_input3.yaml"
    hex0 = HeatExc(inp, "condenser")
    
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
