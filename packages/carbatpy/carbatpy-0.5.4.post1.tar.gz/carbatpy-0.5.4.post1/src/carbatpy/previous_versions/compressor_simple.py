# -*- coding: utf-8 -*-
"""
Class FlowDevice
functions for compressor and expander output state calcultations

so far/here: only for fixed isentropic efficiencies
pumps and throttles added.

((Part of carbatpy.))
Created on Sun May 21 08:51:33 2023

@author: atakan
"""

import carbatpy as cb
import numpy as np


class FlowDevice:
    """Unified themodynamic calculations for single flow devices"""
    def __init__(self, fluid, p_out, m_dot, device_type="machine", **kwargs):
        """
        Calculate the output state and state changes for single flow devices

        Parameters
        ----------
        fluid : Fluid
            The fluid at is entering state.
        p_out : float
            Output pressure in Pa.
        m_dot : float
            mass flow rate in kg/s.
        device_type : TYPE, optional
            'machine' for compressor/expander, 'pump', or 'throttle'. The default is
            "machine".
        **kwargs : dictionary
            Optional parameters for setting the configuration and parameters
            
            - plot info : dictionary,optional, default value is {} contains a Figure, an 
                Axes, a list of What shall be plotted,
                a list with the colour/styles and a list with the labels must be
                passed. in "what", the two numbers coincide with the fluid THERMO
                order. The x-shift can be used in cycle calculations, to shift the
                curves, by the value (it will be added).
                The names in the dictionary are: "fig", "ax", "what","col",
                "label", "x-shift".
            - name : string, optional, the name of this specific device, the default is
                "compressor".
            - calc_type : string, optional, which method shall be used (e.g.: "const_eta",
                "const_h"), default is "const_eta".
            - calc_parameters : dictionary, optional, if further parameters have to be
                given for the calculation. the default is None.
            - verbose : Boolean, optional, the default is False.
            
            
            DESCRIPTION.
            the self.output dictionary contains the exit state values, and work and power.
            The self.fluid is at the exit state. Check self.warning and self.warning_message.
            There is also a self.print_device function for inspection. If a figure is passed
            by plot_info the plot will be updated.

        Returns
        -------
        None.

        """
        self.fluid = fluid
        self.p_out = p_out
        self.m_dot = m_dot
        self.device_type = device_type
        self.plot_info = kwargs.get("plot_info", {})
        self.name = kwargs.get("name", "compressor")
        self.calc_type = kwargs.get("calc_type", "const_eta")
        self.calc_parameters = kwargs.get("calc_parameters", None)
        self.verbose = kwargs.get("verbose", False)
        self.warning = 0
        self.warning_message = "All o.k."
        self.input = fluid.properties.state
        self.output = None

        match device_type:  # noeq
            case "machine":
                self.compressor()
            case "pump":
                self.pump()
            case "throttle":
                self.throttle()
            case _:
                print(f"Not implemented device: {device_type}")

    def compressor(self):
        """
        compressor or expander output state calculation

        so far only for a constant isentropic efficiency, according to the pressure
        change an expansion or compression is detected and handled.

        Parameters
        ----------

        p_out : float
            output pressure.
        eta_s : float
            isentropic efficiency.
        fluid : fprop.Fluid
            entering fluid, including properties, composition, and model.
        m_dot : float, optional
            mass flow rate (in kg/s). Default is 1
        calc_type : string, optional
            how to calculate, so far, only one implemented. The default is
            "const_eta".
        name : string, optional
            name of the device. The default is "compressor".
        plot_info : dictionary, optional
            if not empty a Figure, an Axes, a list of What shall be plotted,
            a list with the colour/styles and a list with the labels must be
            passed. in "what", the two numbers coincide with the fluid THERMO
            order. The x-shift can be used in cycle calculations, to shift the
            curves, by the value (it will be added).
            The names in the dictionary are: "fig", "ax", "what","col",
            "label", "x-shift". Default is empty.

        Returns
        -------
        state_out : array of float
            compressor output state containing [T,p,h,v,s,q].
        work_specific : float
            work per kg of fluid, positive for compressor; units:J/kg.

        """
        state_in = self.fluid.properties.state
        expander = False
        if self.fluid.properties.pressure > self.p_out:
            expander = True

        if self.calc_type == "const_eta":
            if self.calc_parameters["eta_s"]:
                eta_s = self.calc_parameters["eta_s"]
            else:
                self.warning = 99
                self.warning_message = f"No 'eta_s' provided, a value of 1 will be used!"
                self.calc_parameters["eta_s"] = eta_s = 1.0

            self.fluid.set_state(
                [self.fluid.properties.entropy, self.p_out], "SP")

            diff_enthalpy_s = self.fluid.properties.enthalpy-state_in[2]

            if expander:
                work_specific = diff_enthalpy_s * eta_s
            else:
                work_specific = diff_enthalpy_s / eta_s

            state_out = self.fluid.set_state(
                [state_in[2] + work_specific, self.p_out], "HP")

        else:
            self.warning = 100
            self.warning_message = f""""The option{calc_type} is not yet implemented for
            compressors"""
            raise Exception(
                self.warning_message)

        power = self.m_dot * work_specific

        #
        self.output = {"state_out": state_out,
                       "work_specific": work_specific,
                       "power": power}
        self.plot_temp_h_flow()

    def pump(self):
        """
        Calculate the exit state of a pump assuming an incompressible fluid.

        Only formulated for constant isentropic efficiency

        Parameters
        ----------
        p_out : float
            output pressure.
        eta_s : float
            isentropic efficiency.
        fluid : fprop.Fluid
            entering fluid, including properties, composition, and model.
        m_dot : float, optional
            mass flow rate (in kg/s). Default is 1
        calc_type : string, optional
            how to calculate, so far, only one implemented. The default is
            "const_eta".
        name : string, optional
            name of the device. The default is "pump".
        plot_info : dictionary, optional
            if not empty a Figure, an Axes, a list of What shall be plotted,
            a list with the colour/styles and a list with the labels must be
            passed. in "what", the two numbers coincide with the fluid THERMO
            order. The x-shift can be used in cycle calculations, to shift the
            curves, by the value (it will be added).
            The names in the dictionary are: "fig", "ax", "what","col",
            "label", "x-shift". Default is empty.

        Returns
        -------
        state_out : array of float
            compressor output state containing [T,p,h,v,s,q].
        work_specific : float
            work per kg of fluid, positive for compressor; units:J/kg.

        """
        state_in = self.input
        if self.calc_type == "const_eta":

            if self.calc_parameters["eta_s"]:
                eta_s = self.calc_parameters["eta_s"]
            else:
                self.warning = 99
                self.warning_message = f"No 'eta_s' provided, a value of 1 will be used!"
                self.calc_parameters["eta_s"] = eta_s = 1.0

            work_is = state_in[3] * (self.p_out - state_in[1])
            if work_is > 0:
                work_specific = work_is / eta_s
            else:
                work_specific = work_is * eta_s
            h_out = state_in[2] + work_specific
            state_out = self.fluid.set_state([h_out, self.p_out], "HP")
        else:
            self.warning = 130
            self.warning_message = f"The option{calc_type} is not yet implemented for pumps"
            raise Exception(self.warning_message)
        power = self.m_dot * work_specific

        self.output = {"state_out": state_out,
                       "work_specific": work_specific,
                       "power": power}
        self.plot_temp_h_flow()

    def throttle(self):
        """
        throttle output state calculation

        so far only for a constant enthalpy

        Parameters
        ----------
        p_out : float
            output pressure.
        fluid : fprop.Fluid
            entering fluid, including properties, composition, and model.
        m_dot : float, optional
            mass flow rate (in kg/s). Default is 1
        calc_type : string, optional
            how to calculate, so far, only one implemented. The default is
            "const_h".
        name : string, optional
            name of the device. The default is "throttle".
        plot_info : dictionary, optional
            if not empty a Figure, an Axes, a list of What shall be plotted,
            a list with the colour/styles and a list with the labels must be
            passed. in "what", the two numbers coincide with the fluid THERMO
            order. The x-shift can be used in cycle calculations, to shift the
            curves, by the value (it will be added).
            The names in the dictionary are: "fig", "ax", "what","col",
            "label", "x-shift". Default is empty.

        Returns
        -------
        state_out : array of float
            compressor output state containing [T,p,h,v,s,q].

        """
        state_in = self.fluid.properties.state
        if self.calc_type == "const_h":
            state_out = self.fluid.set_state([self.fluid.properties.enthalpy,
                                              self.p_out], "HP")
        else:
            raise Exception(
                f"The option{self.calc_type} is not yet implemented for throttles")

        self.output = {"state_out": state_out,
                       "work_specific": 0.0,
                       "power": 0.0}
        self.plot_temp_h_flow()

        #
        return state_out

    def plot_temp_h_flow(self):
        """
        plotting a T-H-dot diagram for simple flows (compressor, throttle etc.)

        Parameters
        ----------
        _state_in : np.array
            entering state [T,p,h,v,s,...].
        _state_out : np.array
            exiting state.
        _m_dot : float
            mass flow rate (kg/s).
        _plot_info : dictionary
            if not empty a Figure, an Axes, a list of What shall be plotted,
            a list with the colour/styles and a list with the labels must be
            passed. in "what", the two numbers coincide with the fluid THERMO
            order. The x-shift can be used in cycle calculations, to shift the
            curves, by the value (it will be added).
            The names in the dictionary are: "fig", "ax", "what","col",
            "label", "x-shift".

        Returns
        -------
        None.

        """
        if len(self.plot_info) > 0:
            if self.plot_info["what"][0] == 2:
                data = np.array([self.input[self.plot_info["what"][0]],
                                 self.output["state_out"][self.plot_info["what"][0]]]) * self.m_dot \
                    + self.plot_info["x-shift"][0]
                self.plot_info["ax"].plot(data,
                                          [self.input[self.plot_info["what"][1]],
                                           self.output["state_out"][self.plot_info["what"][1]]],
                                          self.plot_info["col"][0],
                                          label=self.plot_info["label"][0])
            else:
                self.warning = 130
                self.warning_message = f"Pump: plotting only implemented fot T-H_dot [2,0]. You requested{_plot_info['what']}"
                print(self.warning_message)

    def print_device(self):

        print(f"\nDevice: {self.device_type}, {self.calc_type}")
        print(f"Parameters, {self.calc_parameters}")
        print(f"Input, {self.input}")
        print(f"Output: {self.output}")
        if self.warning:
            print(f"Device: {self.warning}, {self.warning_message}")


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    FLUID = "Propane * Pentane"
    comp = [.80, 0.2]
    flm = cb.fprop.FluidModel(FLUID)
    myFluid = cb.fprop.Fluid(flm, comp)
    P_LOW = 1e5
    T_IN = 310.
    DT_IN_LIQ = -5
    state_in_act = myFluid.set_state([T_IN, P_LOW], "TP")
    P_OUT = 10e5
    ETA_S = .7
    M_DOT = 1e-3
    fig0, ax0 = plt.subplots()
    PLOT_INFO = {"fig": fig0, "ax": ax0, "what": [2, 0], "col": ["r:", "k"],
                 "label": ["compressor", "xx"], "x-shift": [0, 0]}

    # Compressor-------------
    compressor = FlowDevice(myFluid, P_OUT, M_DOT,
                            device_type="machine",
                            name="compressor",
                            calc_type="const_eta",
                            calc_parameters={"eta_s": ETA_S},
                            plot_info=PLOT_INFO)
    # state_o, work, power_c = compressor(myFluid, P_OUT, M_DOT, ETA_S, device_type="machine",
    # plot_info=PLOT_INFO)
    print(myFluid.properties.temperature, compressor.output)
    # print("\nCompressor", state_in_act, "\n", state_o, "\n", state_o-state_in_act)
    PLOT_INFO["col"] = ["k", ""]
    PLOT_INFO["label"] = ["expander", ""]

    expander = FlowDevice(myFluid, P_LOW, M_DOT,
                          device_type="machine",
                          name="expander",
                          calc_type="const_eta",
                          calc_parameters={"eta_s": ETA_S},
                          plot_info=PLOT_INFO)
    print("\nExpander:", expander.output)

    # Pump, incompressible:

    state_in_p = myFluid.set_state([P_LOW, 0], "PQ")
    state_in_p = myFluid.set_state([P_LOW, state_in_p[0]+DT_IN_LIQ], "PT")
    PLOT_INFO["col"] = ["bv:", ""]
    PLOT_INFO["label"] = ["pump", ""]
    pump = FlowDevice(myFluid, P_OUT, M_DOT,
                      device_type="pump",
                      name="pump-A",
                      calc_type="const_eta",
                      calc_parameters={"eta_s": ETA_S},
                      plot_info=PLOT_INFO)
    print(
        f"pump work output: {pump.output['work_specific']:.3f} J/kg, \npump all:{pump.output}")
    
    # throttle:
    PLOT_INFO["col"] = ["go:", ""]
    PLOT_INFO["label"] = ["throttle", ""]
    state_in_p = myFluid.set_state([P_OUT, state_in_p[0]+DT_IN_LIQ], "PT")
    throttle = FlowDevice(myFluid, P_OUT, M_DOT,
                          device_type="throttle",
                          name="throttle-A",
                          calc_type="const_h",
                          calc_parameters={},
                          plot_info=PLOT_INFO)
    throttle.print_device()
    
    # if you want a legend etc
    ax0.legend()
    ax0.set_ylabel("T/K")
    ax0.set_xlabel("$\dot h$/ kW")
