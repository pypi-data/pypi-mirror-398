# -*- coding: utf-8 -*-
"""
Created on Mon May 22 21:09:12 2023

@author: atakan
"""

import os
import copy
# from time import time
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import numpy as np
# import CoolProp.CoolProp as CP
import carbatpy

VERBOSE = False
DEFAULTS = carbatpy.CB_DEFAULTS
TREND = DEFAULTS['Fluid_Defaults']['TREND']

if TREND["TREND_INSTALLED"]:
    trend_dll = TREND["TREND_DLL"]
    trend_path = TREND["TREND_PATH"]
    try:
        import fluid as tr_fl  # TREND fluids

    except ImportError as e:
        print(f"Import error for 'fluid': {e}")


# os.environ['RPPREFIX'] = r'C:/Program Files (x86)/REFPROP'
# os.environ['RPPREFIXs'] = r'C:/Program Files (x86)/REFPROP/secondCopyREFPROP'
<<<<<<< HEAD
_PROPS = "REFPROP"  # or "CoolProp"

_fl_properties_names = ("Temperature", "Pressure", "spec_Enthalpy",
                        "spec_Volume", "spec_Entropy", "quality",
                        "spec_internal_Energy", "viscosity", "thermal_conductivity",
                        "Prandtl_number",
                        "specific isobaric heat capacity",
                        "molecular_mass", "speed_of_sound",
                        )
_THERMO_STRING = "T;P;H;V;S;QMASS;E"
_THERMO_TREND = request = ["T", "P", "H", "D",
                           "S", "QEOS", "U"]  # careful density not volume
_THERMO_LEN = len(request)
_TRANS_STRING = _THERMO_STRING + ";VIS;TCX;PRANDTL;CP;M;W"
_TRANS_TREND = copy.copy(_THERMO_TREND)
_TRANS_TREND.extend(["ETA", "TCX", "CP", "WS"])
_TV_STRING = "T;V"
_T_SURROUNDING = 288.15  # K
=======
_PROPS = DEFAULTS["Fluid_Defaults"]['PROPS']  # "REFPROP"  # or "CoolProp"

_fl_properties_names = DEFAULTS["Fluid_Defaults"]['Property_Names']
_THERMO_STRING = DEFAULTS["Fluid_Defaults"]['THERMO_STRING']
_THERMO_TREND = request =DEFAULTS["Fluid_Defaults"]['THERMO_TREND']  # careful density not volume
_TRANS_STRING = DEFAULTS["Fluid_Defaults"]['TRANS_STRING']
_TRANS_TREND = DEFAULTS["Fluid_Defaults"]['TRANS_TREND']


_T_SURROUNDING = DEFAULTS["General"]['T_SUR'] # K
>>>>>>> Branch_0.3.1
_MODEL_ARGS = {}

# order for coolprop,alle_0:[_temp, p,  h, 1/ rho, s,x,cp, mu,  lambda_s,
# prandtl, phase]"
SPECIFIC_RP = 21
_UNITS = SPECIFIC_RP
rp_instance = ""

if _PROPS == "REFPROP":
    DLL_SELECT = DEFAULTS["Fluid_Defaults"]['DLL_SELECT']
    try:
        rp_instance = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
        # be careful pressure is in Pa!
        _UNITS = rp_instance.GETENUMdll(0, DEFAULTS["Fluid_Defaults"]['UNITS']).iEnum
    except:  # ModuleNotFoundError as errefprop:
        print(f"Refprop is not installed!")  # " {errefprop}")
elif _PROPS == "TREND":
    pass
else:
    print(f"_PROPS value, not installed {_PROPS}")


class FluidModel:
    """
    Fluid model to be used Refprop or TREND

    Only model, chemical compunds units and for TREND some more values are set here. The
    mixture composition, state etc. is set in Fluid.
    """

    def __init__(self, fluid, units=_UNITS, props=_PROPS, rp_inst=rp_instance,
                 args=_MODEL_ARGS):
        """
        For Class Fluidmodell a fluid (mixture) must be defined, the evaluation
        takes place with props, units can be set and an instance can be set,
        the latter is important, if more than one fluid is used.

        Parameters
        ----------
        fluid : String
            as defined in the props (Model), for RefProp it is
            "fluid1 * fluid2 * fluid3".
        units : integer, optional
            units, normally SI wuth MASS base, see props(RefProp).
            The default is _UNITS.
        props : string, optional
            select the property model. The default is _PROPS.
        rp_inst : RefProp-Instance, optional
            where Refprop is installed, for two fluids, as in heat exchangers,
            two installations/instances are needed. The default is rp_instance.
        args : Dictionary, optional
            Further arguments passed to the module used for fluid property
            evaluation. for props =="REFPROP" nothing is needed. The default is
            the empty dictionary _MODEL_ARGS.

        Returns
        -------
        None.

        """
        self.fluid = fluid
        self.props = props
        self.units = units
        self.args = args
        if props == "REFPROP":
            self.rp_instance = rp_inst
            self.set_rp_fluid()
        elif props == "TREND":
            self.set_tr_fluid()

    def set_rp_fluid(self, modwf=REFPROPFunctionLibrary, name='RPPREFIX'):
        """
        A new instance of Refpropdll for the given fluid. It can then be called
        using fluid =""

        Parameters
        ----------
        fluid : string
            fluid (mixture) name, as described in REFPROP.

        Returns
        -------
        self.rp_instance : REFPROP Instance
            for further usage.

        """

        self.rp_instance = modwf(os.environ[name])
        self.rp_instance.SETPATHdll(os.environ[name])
        ierr = self.rp_instance.SETFLUIDSdll(self.fluid)
        if ierr != 0:
            print(f"Fehler in setfluid {ierr}")
            print(self.rp_instance.ERRMSGdll(ierr))
        return self.rp_instance

    def set_tr_fluid(self):
        self.fluid = self.fluid_to_list()
        if self.units == SPECIFIC_RP:
            self.units = "specific"

        n_compounds = len(self.fluid)
        if len(self.args["moles"]) < n_compounds:
            self.args["moles"] = list(np.zeros(n_compounds))
            self.args["moles"][0] = 1.
        if len(self.args["eos_ind"]) < n_compounds:
            self.args["eos_ind"] = list(np.ones(n_compounds))
        if self.args["mix_ind"] < 1:
            self.args["mix_ind"] = 1

        _trend_dict = {"Input": "TP",
                       'calctype': "H",
                       'fluids': self.fluid,
                       "moles": self.args["moles"],
                       "eos_ind": self.args["eos_ind"],
                       'mix_ind': self.args["mix_ind"],
                       'path': trend_path,
                       'unit': self.units,
                       'dll_path': trend_dll}

        self.rp_instance = tr_fl.Fluid(*_trend_dict.values())
        err_flag = self.rp_instance.errorflag.value
        if err_flag > 0:
            print(f"fluid-Trend problem, errorflag:{err_flag}")
        return self.rp_instance

    def fluid_to_list(self):
        """
        conversts the fluid names string from Refprop to list for TREND

        Returns
        -------
        List of strings
            the fluid names in a list.

        """
        no_blank = self.fluid.replace(" ", "")
        return no_blank.split("*")


<<<<<<< HEAD
=======
class FluidState:
    """
    The thermodynamic state of a fluid is stored here
    """

    def __init__(self, state, what, **kwargs):
        self.props = kwargs.get("props", _PROPS)
        self. verbose = kwargs.get("verbose", False)
        self.liq_x = kwargs.get("x", None)
        self.vap_y = kwargs.get("y", None)
        self.total_z = kwargs.get("z", None)

        self.no_val = what.count(";")+1
        self.temperature = state[0]
        self.pressure = state[1]
        self.sp_volume = state[3]
        self.enthalpy = state[2]
        self.entropy = state[4]
        self.quality = state[5]
        self.int_energy = state[6]
        self.state = state[:7]
        self.prop_names = _fl_properties_names
        if self.verbose:
            print(what, no_val, state)

        if self.no_val > 7 and self.props in ("REFPROP",):
            # ";VIS;TCX;PRANDTL;KV;M;W"
            self.viscosity = state[7]
            self.thermal_conductivity = state[8]
            self.prandtl = state[9]
            self.kin_viscosity = state[10]
            self.molecular_mass = state[11]
            self.speed_of_sound = state[12]
            self.transport = state[7:13]
            self.state = state[:13]

    def state_to_dict(self):
        return_dict = dict(zip(_fl_properties_names[:self.no_val], self.state[:self.no_val]))
        return_dict["x"] = self.liq_x
        return_dict["y"] = self.vap_y
        return_dict["z"] = self.total_z
        return  return_dict


>>>>>>> Branch_0.3.1
class Fluid:
    """
    The Fluid class is used to set, get, and print states of  a fluid with a given

    model (e.g. RefProp). The compounds are set in the fluidmodel, while the
    composition is also set here.

    """

    def __init__(self, fluidmodel, composition=None, option=1):
        """
        Generate a Fluid instance

        a FluidModel instance, the composition and an unused option has to be passed.

        Parameters
        ----------
        fluidmodel : FluidModel
            the instance of the property model to be used.
        composition : list, optional
            mole fractions of all compounds. The default is [1.0].
        option : TYPE, optional
            unused. The default is 1.

        Returns
        -------
        None.

        """

        self.fluidmodel = fluidmodel
<<<<<<< HEAD
        
=======
        if composition is None:
            composition = [1.0]
        else:
            self.composition = composition
        self.composition = copy.copy(composition)
>>>>>>> Branch_0.3.1
        self.properties = None
        self.state_v = None
        self.option = option
        
        
        self.herr = 0
        self.props = fluidmodel.props
<<<<<<< HEAD
        self.temperature = None
        self.pressure = None
        self.enthalpy = None
        self.sp_volume = None
        self.entropy = None
        self.quality = None
        self.int_energy = None
        self.state = []
    
        self.viscosity = None
        self.thermal_conductivity = None
        self.prandtl = None
        self.cp = None
        self.molecular_mass = None
        self.speed_of_sound = None
        self.transport = []
        if composition is None:
            self.composition = [1.0]
        self.comp_mole = copy.copy(composition)
        self.no_compounds = len(composition)
        self.set_composition(composition)
        
        #self.comp_mass = np.zeros(self.no_compounds)
        if self.props == "TREND":
            # important for trend mass->mole"
            
=======
        # BA something is wrong here (probably 2024-07-10
        self.set_composition(composition)
        if self.props == "TREND":
            # important for trend mass->mole"

>>>>>>> Branch_0.3.1
            self.fluidmodel.rp_instance.set_moles(self.composition)
            if VERBOSE:
                print("Konversion", self.composition,
                      self.comp_mass,
                      self.composition,
                      self.fluidmodel.rp_instance.get_moles())

    def set_composition(self, composition, **kwargs):
        """
        Mainly for TREND mole fractions have to converted to mass fractions

        Sets the self.composition used in the Fluid settings and the self.comp_mass
        and self.composition by calling calc_mass_fraction()

        Parameters
        ----------
        composition : list/numpy.array
            mole fractions must sum up to 1.

        Returns
        -------
        None.

        """
        verbose = kwargs.get("verbose", False)
        if verbose:
            print("set_comp", composition, self.composition, self.comp_mass)
        self.composition = composition
        if self.fluidmodel.props == "TREND":
            self.comp_mass = composition
            self.calc_mass_fraction()
            self.fluidmodel.rp_instance.set_moles(self.composition)
        elif self.fluidmodel.props == "REFPROP":
            self.comp_mass = self._rp_mass_from_mole(composition)
            
            # here is the mass fraction to internal mol fraction conversion
        elif self.fluidmodel.props == "REFPROP":
            self.comp_mass = self._rp_mass_from_mole(composition)
        if verbose:
            print("set_comp-after", composition, self.composition, self.comp_mass)

    def calc_mass_fraction(self):
        """ mole to mass fractions for TREND"""
        mass_frac = np.zeros(self.no_compounds)
        for n_c in range(self.no_compounds):
            mass_frac[n_c] = self.fluidmodel.rp_instance.get_mw(n_c) * \
                self.composition[n_c]
        self.comp_mass = mass_frac/mass_frac.sum()
        self.composition = copy.copy(self.comp_mass)
        return self.composition

    def set_state(self, values, given="TP", wanted=_THERMO_STRING, composition=None,
                  **kwargs):
        """
        Sets the state of a fluid and calculates the wanted

        Parameters
        ----------
        values : list[2]
            the two state parameter values.
        given : String, optional
            What are the two values (T,P,H,S,Q,V). The default is "TP".
        wanted : String, optional
            Which parameters shall be calculated? The default is _THERMO_STRING.
        composition : list, optional
            mole fraction of each compound, must sum up to 1. When empty, the last/actual
            value  will be used. The default is [].
        kwargs : dictionary, optional
            Flags like iMass or iFlag can be passed to Refprop. with iMass=1 the input
            composition is taken as mass fraction, otherwise they are mole fractions. iMass
            is set to 1 if 'Q' is in wanted.
            if full_dll=True the REFPROPdll is called REFPROP2dll otherwise! The default
            is False)

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.
        """

        composition = self._update_composition(composition)

        if self.fluidmodel.props == "REFPROP":
            self._set_state_refprop(values, given, wanted, composition, **kwargs)
        elif self.fluidmodel.props == "TREND":
            self._set_state_trend(values, given, wanted)
        else:
            raise NotImplementedError(
                f"Property model {self.fluidmodel.props} not implemented yet!")

        return np.array([*self.state])

    def _update_composition(self, composition):
        if composition is None:  # mole fractions only!
            return self.composition

<<<<<<< HEAD
        # self.composition = composition
    
        self.set_composition(composition)  # important for trend mass->mole
        if VERBOSE:
            print("comp-set", composition, self.composition,
                  self.comp_mass, self.comp_mole)
        return composition

    def _set_state_refprop(self, values, given, wanted, composition, **kwargs):
        i_mass = kwargs.get("iMass", 1)
        i_flag = kwargs.get("iFlag", 0)
        full_dll = kwargs.get("full_dll", True)
        to_mole = False

        if i_mass == 0 and i_flag == 0 and not full_dll:
            state = self.fluidmodel.rp_instance.REFPROP2dll(
                self.fluidmodel.fluid, given, wanted,
                self.fluidmodel.units,
                i_flag, values[0], values[1],
                composition
            )
        elif i_mass ==1 and self.fluidmodel.units==_UNITS:  # the standard way of property calculations MASS UNITS
            state = self.fluidmodel.rp_instance.REFPROPdll(
                self.fluidmodel.fluid, given, wanted,
                self.fluidmodel.units,
                i_mass,
                i_flag, values[0], values[1],
                self.comp_mass
            )
            to_mole =True
        else:
            state = self.fluidmodel.rp_instance.REFPROPdll(
                self.fluidmodel.fluid, given, wanted,
                self.fluidmodel.units,
                i_mass,
                i_flag, values[0], values[1],
                self.comp_mass
            )
            print("Warning: This REFPROP flag combination was not checked!")
=======
        self.set_composition(composition)  # important for trend mass->mole
        if VERBOSE:
            print("comp-set", composition, self.composition,
                  self.comp_mass, self.composition)
        return composition

    def _set_state_refprop(self, values, given, wanted, composition, **kwargs):
        i_mass = kwargs.get("iMass", 0)
        i_flag = kwargs.get("iFlag", 0)  # if this is 1 most tests fail!
        dll_select = kwargs.get("dll_select", "2dll")
        verbose = kwargs.get("verbose", False)

        match dll_select:  # noqa
            case "2dll":
                i_mass=0
                state = self.fluidmodel.rp_instance.REFPROP2dll(
                    self.fluidmodel.fluid, given, wanted,
                    self.fluidmodel.units,
                    i_flag, values[0], values[1],
                    copy.copy(self.composition)
                )
            case "dll":
                i_mass=1
                state = self.fluidmodel.rp_instance.REFPROPdll(
                    self.fluidmodel.fluid, given, wanted,
                    self.fluidmodel.units,
                    i_mass,
                    i_flag, values[0], values[1],
                    copy.copy(self.composition)
                )
                
                if verbose:
                    print(state.z[:5], self.composition, self.comp_mass)
            case _:
                raise ValueError(f"This iMass value is not allowed {i_mass}")
>>>>>>> Branch_0.3.1

        if state.ierr == 0:
            state_val = state.Output
            z_act = state.z[:self.no_compounds]
            x_act = y_act = None

            if state.q > 0 and state.q < 1:  # mole -> mass quality problem of Refprop
<<<<<<< HEAD
                state_val[5] = state.q
                if full_dll:
                    x_act = state.x[:self.no_compounds]
                    y_act = state.y[:self.no_compounds]
                    if to_mole:  # convert back to mole fractions
                        x_act = self._rp_mole_from_mass(state.x)
                        y_act = self._rp_mole_from_mass(state.y)
                        z_act = self._rp_mole_from_mass(state.z)

                # self.properties
            self._set_fluid_properties(state_val,
                                       wanted,
                                       x=x_act,
                                       y=y_act,
                                       z=z_act)
            # if wanted == _THERMO_STRING:
            #     self.properties = FluidState(state_val)
            # elif wanted == _TRANS_STRING:
            #     self.properties = FluidStateTransport(state_val)
            # elif wanted == _TV_STRING:
            #     self.properties = FluidStateTV(state_val)
            # else:
            #     raise NotImplementedError(f"properties {wanted} not implemented yet!")
=======
                # state_val[5] = state.q
                if dll_select == "dll":
                    x_act = state.x[:self.no_compounds]
                    y_act = state.y[:self.no_compounds]
                    if _UNITS == 21:  # convert back to mole fractions
                        x_act = self._rp_mole_from_mass(state.x)
                        y_act = self._rp_mole_from_mass(state.y)
                        z_act = self._rp_mole_from_mass(state.z)
            self.properties = FluidState(state_val, wanted, x=x_act, y=y_act, z=z_act)
            self.val_dict = self.properties.state_to_dict()

>>>>>>> Branch_0.3.1
        else:
            self.herr = state.herr
            raise RuntimeError(f"Property-Refprop problem: {state.herr}!")

    def _rp_mass_from_mole(self, composition):
        return self.fluidmodel.rp_instance.XMASSdll(composition).xkg[:self.no_compounds]

    def _rp_mole_from_mass(self, composition):
        return self.fluidmodel.rp_instance.XMOLEdll(composition).xmol[:self.no_compounds]

    def _set_state_trend(self, values, given, wanted):
        if VERBOSE:
            print("in TREND set state")

        values, given = self._adjust_trend_values(values, given)
        all_values = self.fluidmodel.rp_instance.ALLPROP(given, values[0], values[1])
        all_val_initial = copy.copy(all_values)

        if all_values["T"] > 0:  # on error it is -8888
            all_values["P"] = all_values["P"] * 1e6  # MPa
            all_values["D"] = 1 / all_values["D"]  # V (spec. volume)
            all_values = [all_values[key] for key in _THERMO_TREND]
            if wanted == _TRANS_STRING:

                trans_dict = {}
                speed_sound = all_val_initial["WS"]
                for tr_want in _TRANS_TREND[-3:]:
                    self.fluidmodel.rp_instance.set_calctype(tr_want)
                    self.fluidmodel.rp_instance.set_input(given)

                    trans_dict[tr_want], err = self.fluidmodel.rp_instance.TREND_EOS(
                        *values)
                    print(tr_want, ":", trans_dict[tr_want], err)
                    if trans_dict[tr_want] < 0:
                        print("WARNING: Problem / NOT IMPLEMENTED IN TREND!")

<<<<<<< HEAD
            # self.properties = FluidState(all_values)
            self._set_fluid_properties(all_values,
                                       wanted)
=======
            self.properties = FluidState(all_values, wanted, props="TREND")
            self.val_dict = self.properties.state_to_dict()
>>>>>>> Branch_0.3.1
        else:
            raise RuntimeError(
                f"property calculation in TREND failed, error code TREND: {all_values['T']}")

    def _adjust_trend_values(self, values, given):
        pressure_in = given[:2].find("P")
        quality_in = given[:2].find("Q")
        temp_in = given[:2].find("T")

        if pressure_in >= 0:
            values[pressure_in] = values[pressure_in] / 1e6  # MPa in Trend
        if quality_in > 0:
            if pressure_in >= 0:
                values, given = self._adjust_values_for_quality_pressure(
                    values, quality_in, pressure_in)
            elif temp_in >= 0:
                values, given = self._adjust_values_for_quality_temperature(
                    values, quality_in, temp_in)
            else:
                raise NotImplementedError(
                    f'Error: Qualities cannot be combined with {given}!')
        return values, given

    def _adjust_values_for_quality_pressure(self, values, quality_in, pressure_in):
        match values[quality_in]:  # noqa
            case 0.:
                given = "PLIQ"
            case 1.:
                given = "PVAP"
            case _:
                raise ValueError('Error: only qualities 0 or 1 for mixtures!')
        values[0] = values[pressure_in]
        values[1] = 10
        return values, given

    def _adjust_values_for_quality_temperature(self, values, quality_in, temp_in):
        match values[quality_in]:
            case 0.:
                given = "TLIQ"
            case 1.:
                given = "TVAP"
            case _:
                raise ValueError('Error: only qualities 0 or 1 for mixtures!')
        values[0] = values[temp_in]
        values[1] = 10
        return values, given

    def set_state_v(self, values, given="TP", wanted=_THERMO_STRING, **kwargs):
        """
        set many Fluid states with the values given as array(vector)

        Parameters
        ----------
        values : numpy.array((N,2))
            the N value pairs to fix the states.
        given : String, optional
            what are the input values?(T,P, Q, S,...). The default is "TP".
        wanted : String, optional
            with all the outputs wanted. The default is _THERMO_STRING.

        Returns
        -------
        output : numpy.array(N, n_wanted)
            all the wanted properties for the N inputs.

        """
        dimension = np.shape(values)
        number_wanted = wanted.count(";")+1
        output = np.zeros((dimension[0], number_wanted))
        for count, value in enumerate(values):
            output[count, :] = self.set_state(value, given, wanted, **kwargs)
        self.state_v = output
        return output

    def _set_fluid_properties(self, state, wanted, **kwargs):
        """
        The thermodynamic state of a fluid is stored here
        """
        self.liq_x = kwargs.get("x", None)
        self.vap_y = kwargs.get("y", None)
        self.total_z = kwargs.get("z", None)
        verbose = kwargs.get("verbose", False)
        n_prop = wanted.count(";")+1
        n_states = len(state)

        if verbose:
            print(n_prop, state)
        # "T;P;H;V;S;QMASS;E"
        self.temperature = state[0]
        self.pressure = state[1]
        self.enthalpy = state[2]
        self.sp_volume = state[3]
        self.entropy = state[4]
        self.quality = state[5]
        self.int_energy = state[6]
        self.state = state[:_THERMO_LEN]
        self.prop_names = _fl_properties_names
        if _THERMO_LEN in (n_prop, n_states):
            return
        else:
            if state[5] > 0 and state[5] < 1:
                two_phase = True
            # ";VIS;TCX;PRANDTL;KV;M"
            self.viscosity = state[7]
            self.thermal_conductivity = state[8]
            self.prandtl = state[9]
            self.cp = state[10]
            self.molecular_mass = state[11]
            self.speed_of_sound = state[12]
            self.transport = state[7:13]
            self.state = state[:13]
            return

    def print_state(self):
        """ Print the actual state of the Fluid"""
        pr = self
        flmod = self.fluidmodel
        print(f"\n{flmod.fluid}, composition: {self.composition}")
        print(f"T:{pr.temperature:.2f} K, p: {pr.pressure/1e5 :.2f} bar,  h: {pr.enthalpy/1000: .2f} kJ/kg, s: {pr.entropy/1000:.3f} kJ/kg K\n")
        if pr.quality >= 0:
            print(f"Quality: {pr.quality :.3f}")

    def calc_temp_mean(self, h_final):
        """
        Calculate the thermodynamic mean temperature between the actual state

        and the final enthalpy along an isobaric (Delta h /Delta s)

        Parameters
        ----------
        h_final : float
            enthalpy of he final stat.

        Returns
        -------
        temp_mean : float
            the thermodynamic mean temperature.

        """
        actual_props = self.state
        final_props = self.set_state([h_final, actual_props[1]], "HP")
        temp_mean = (final_props[2] - actual_props[2]) \
            / (final_props[4] - actual_props[4])
        return temp_mean


def init_fluid(fluid, composition, **keywords):
    """
    short way to define a Fluid and a FluidModel

    Parameters
    ----------
    fluid : string
        The species within the fluid.
    composition : List
        mole fraction for each fluid.
    **keywords : TYPE
        all keywords needed for the FluidModel, if non-defults shall be set.

    Returns
    -------
    actual_fluid : Fluid
        Instance of the actually set Fluid.

    """
    flmod = FluidModel(fluid, **keywords)
    actual_fluid = Fluid(flmod, composition)
    return actual_fluid


if __name__ == "__main__":
    FLUID = "Propane * Pentane"
    comp = [.50, 0.5]
    P_ACT = 1e5
    T_ACT = 370
    flm = FluidModel(FLUID)
    myFluid = Fluid(flm, comp)
    st00 = myFluid.set_state([T_ACT, P_ACT], "TP")
    st1 = myFluid.set_state([T_ACT, P_ACT], "TP",
                            _TRANS_STRING)
    print(st00, st1)
    myFluid.print_state()
    myFluid.set_composition([.2, .8])
    st0 = myFluid.set_state([T_ACT, P_ACT], "TP", composition=[.35, .65])
    myFluid.print_state()

    mean_temp_act = myFluid.calc_temp_mean(st0[2]+1e5)
    print(f"Mean Temperature {mean_temp_act} K")

    # value_vec = np.array([[300, 1e5], [400, 1e5], [500, 1e5]])
    # stv = myFluid.set_state_v(value_vec, "TP")

    # print(myFluid.set_state_v(value_vec, "TP"))
    # print(myFluid.set_state([300., 1.], "TQ"))

    # New simple way to get an instance of Fluid
    myFluid2 = init_fluid(FLUID, comp)

    # Refprop with mass fractions as input
<<<<<<< HEAD
    print('\n------------------------------ Refprop Mole fraction Input, Q as mass ratio')
=======
    print('\n---------------- Refprop Mass fraction Input')
>>>>>>> Branch_0.3.1
    FLUID = "Propane * Pentane"
    comp = [.5, .5]
    myFluid = init_fluid(FLUID, comp)

<<<<<<< HEAD
    QUALITY = 0.5       # is interpreted as kg/kg
    # standard mole fractions for composition, everything else mass based
    st0 = myFluid.set_state([300., QUALITY], "TQ")
=======
    quality = 0.5       # is interpreted by carbatpy as mol/mol to calculate state
    # but given back in string as kg/kg
    st0 = myFluid.set_state([300., quality], "TQ", dll_select="dll")
    myFluid.print_state()
    st0n = myFluid.set_state([st0[1], st0[2]], "PH", dll_select="dll")
    myFluid.print_state()
>>>>>>> Branch_0.3.1

    print(f"quality prescribed: {QUALITY}")
    print(f"resulting quality from carbatpy in st0: {st0[5]}")
    print(st0)
    stb = myFluid.set_state([st0[1], st0[2]], "PH")

    print(f"resulting quality from carbatpy in st0: {stb[5]}")
    print(stb, myFluid.total_z, myFluid.liq_x, myFluid.vap_y)

    print("--------mass")

    # st0 = myFluid.set_state([300., QUALITY], "TQMASS", iMass=1, full_dll=True)

    # print(f"quality prescribed: {QUALITY}")
    # print(f"resulting quality from carbatpy in st0: {st0[5]}")
    # print(st0)
    # stb = myFluid.set_state([st0[1], st0[2]], "PH", iMass=1, full_dll=True)

    # print(f"resulting quality from carbatpy in st0: {stb[5]}")
    # print(stb, myFluid.total_z, myFluid.liq_x, myFluid.vap_y)

    print("\n------------\n")

    # Trend:
    my_dict = {"Input": "TP",
               'calctype': "H",
               'fluids': FLUID,
               "moles": comp,
               "eos_ind": [1, 1],
               'mix_ind': 1,
               'path': trend_path,
               'unit': 'specific',
               'dll_path': trend_dll}
    # comp =[.5,0.5]

    flm_trend = FluidModel(FLUID, props="TREND", args=my_dict)
    # [0.6206645653468038, 0.3793354346531962])
    my_tr_fl = Fluid(flm_trend, comp)
    state_trend = my_tr_fl.set_state([T_ACT, P_ACT], "TP")
    print("\nComparison Refprop vs. Trend\n", st00, "\n", state_trend,
          my_tr_fl.enthalpy)
    state_tr_trans = my_tr_fl.set_state([T_ACT, P_ACT], "TP", wanted=_TRANS_STRING)
    print(f"Trans-String: {state_tr_trans}. Implementation unfinished!")

    # shortcut to generate a trend fluid
    flt0 = carbatpy.init_fluid(FLUID, comp, props="TREND", args=my_dict)

    # saturated mixture:
    state_trend_satp = my_tr_fl.set_state([P_ACT, 0], "PQ")
    print("\nSaturated mixture, liq:\n", state_trend_satp,  my_tr_fl.enthalpy)
    state_trend_satp = my_tr_fl.set_state([P_ACT, 1], "PQ")
    print("Saturated mixture, vap:\n", state_trend_satp,  my_tr_fl.enthalpy)

    # some temperature dependence
    state_trend_c = my_tr_fl.set_state([230., P_ACT], "TP")

    enth = np.linspace(state_trend_c[2], state_trend[2], 29)
    all_props_act = []
    for h_act in enth:

        all_props_act.append(my_tr_fl.set_state([P_ACT, h_act], "PH"))
    all_props_act = np.array(all_props_act)

    import matplotlib.pyplot as plt
    fi, ax = plt.subplots(1)
    ax.plot(all_props_act[:, 2], all_props_act[:, 0])
