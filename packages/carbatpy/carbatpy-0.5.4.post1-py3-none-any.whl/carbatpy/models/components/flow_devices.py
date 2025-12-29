# -*- coding: utf-8 -*-
"""
Started a class for flow devices, especially mixing chambers, but could also be
used for heat exchangers or machines?

at the moment, the only device is for adiabtaic mixing, but also of
fluid mixtures of different compounds and composition.
ouputs as dictionary (state variables to be fixed?)
inputs=list of states (Fluid)
mix = list of 2 lists [[input 1(number), input 2 (number)], [output (number? or different?)]]

Created on Fri May 31 15:16:09 2024

@author: atakan
"""


import copy

# import src.models.fluids.fluid_props as fprop
import numpy as np
from scipy.optimize import minimize  # root, root_scalar
import matplotlib.pyplot as plt
import carbatpy as cb


class MixFlowDevice:

    def __init__(self, inputs, outputs, flow_rates_in, mix=[],
                 name="flow-device",
                 **calc_parameters):
        """
        Flow Device = mixing chamber

        At the moment the species, the mass balance, and the energy balance
        for an adiabatic chanber with given output pressure is calculated. Two
        fluids entering, at the moment only one is exiting.

        Parameters
        ----------
        inputs : list of Fluids
            the (2) fluids entering with the correct states.
        outputs : List of Fluids
            the (actually single) fluid state exiting.
        flow_rates_in : list
            the mass flow rates in kg/s.
        mix : List of two lists, optional
            In the first list the input states are numbered, in the second the
            output states example: [[0,1],[0]]. The default is [].
        name : string, optional
            the name of the device. The default is "flow-device".
        **calc_parameters : dictionary
            example {"calc_type": "HP", "H": "const", "p_out": 1e5}, at the
            moment only p_out values should be changed.

        Returns
        -------
        None.

        """
        self.inputs = inputs
        self.outputs = outputs
        self.flow_rates_in = flow_rates_in
        self.name = name
        # print(mix)
        match len(mix): #noqa
            case 0:
                self.flow_rates_out = flow_rates_in
            case 2:
                self.molecular_weights = []
                self.mix_species = {}
                spec_info = []
                self.n_dot_total = 0
                names = []
                m_flows_list = []
                self.flow_rate_out = [np.array(flow_rates_in).sum()]
                enthalpy_total = []

                for i_in in mix[:][0]:
                    act_info = []
                    state_act = inputs[i_in].properties.state
                    state_act = inputs[i_in].set_state([state_act[1],
                                                        state_act[2]], "PH",
                                                       cb.fprop._TRANS_STRING)
                    molecular_weight = inputs[i_in].properties.molecular_mass
                    n_dot = molecular_weight * flow_rates_in[i_in]
                    self.n_dot_total += n_dot
                    names.extend(inputs[i_in].fluidmodel.fluid_to_list())
                    mole_frac = inputs[i_in].composition
                    mol_flows = np.array(mole_frac) * n_dot
                    m_flows_list.extend(list(mol_flows))
                    enthalpy_total.append(state_act[2] * n_dot)

                all_species = dict.fromkeys(names, 0)

                m_flows = np.array(m_flows_list) / self.n_dot_total

                enthalpy_out = (np.array(enthalpy_total) /
                                self.n_dot_total).sum()

                # print(m_flows.sum(), m_flows, enthalpy_out)

                for i_spec, spec in enumerate(names):
                    all_species[spec] += m_flows[i_spec]
                # all_species.extend(inputs[i_in].fluidmodel.fluid_to_list())
                self.all_species = all_species
                rp_names = "*".join(list(self.all_species.keys()))
                st_mix = cb.fprop.init_fluid(rp_names, list(all_species.values()))
                # st_mix= cb.fprop.Fluid(fl_mix,
                #                        list(my_flow_dev.all_species.values()))

                self.outputs[mix[1][0]] = st_mix
                match calc_parameters["calc_type"]:
                    case "HP":
                        if calc_parameters["H"] == "const":
                            self.st_out = st_mix.set_state([enthalpy_out,
                                                            calc_parameters["p_out"]],
                                                           calc_parameters["calc_type"])
                    case _:
                        self.warning = 998
                        print(
                            f"FlowDevice: calcukation type not implemented: {calc_parameters['calc_type']}")

            case _:
                self.warning = 999
                print(f"FlowDevice: not implemented for length of mix: {mix}")

        #


if __name__ == "__main__":
    FLUID = "Propane * Pentane"
    comp = [.50, 0.5]
    myFluid = cb.fprop.init_fluid(FLUID, comp)
    calc_parameters_act = {"calc_type": "HP", "H": "const", "p_out": 1e5}

    st0 = myFluid.set_state([300., 1e5], "TP")
    FLUID2 = "Propane * Ethane"
    comp2 = [.50, 0.5]
    secFluid = cb.fprop.init_fluid(FLUID2, comp2)
    st0 = secFluid.set_state([400., 1e5], "TP")
    inputs_act = [myFluid, secFluid]
    outputs_act = [myFluid]
    mix_act = [[0, 1], [0]]
    flows_act = [.01, .02]
    my_flow_dev = MixFlowDevice(inputs_act, outputs_act, flows_act, mix_act,
                             **calc_parameters_act)
    print(my_flow_dev.all_species, my_flow_dev.st_out)
