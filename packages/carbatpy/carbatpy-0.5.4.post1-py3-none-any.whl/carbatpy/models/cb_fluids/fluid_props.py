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
    trend_path_base = os.environ['TREND_PATH']
    

    # If a sub-path is defined, append it to TREND_PATH
    if TREND["TREND_SUB_PATH"] is not None:
        trend_path = os.path.join(TREND["TREND_PATH_BASE"], TREND["TREND_SUB_PATH"])
    
    try:
        import fluid as tr_fl  # TREND fluids

    except ImportError as e:
        print(f"Import error for 'fluid': {e}")


# os.environ['RPPREFIX'] = r'C:/Program Files (x86)/REFPROP'
# os.environ['RPPREFIXs'] = r'C:/Program Files (x86)/REFPROP/secondCopyREFPROP'
_PROPS = DEFAULTS["Fluid_Defaults"]['PROPS']  # "REFPROP"  # or "CoolProp"

_fl_properties_names = DEFAULTS["Fluid_Defaults"]['Property_Names']
_fl_properties_names_trend = DEFAULTS["Fluid_Defaults"]['Property_Names_Trend']
_THERMO_STRING = DEFAULTS["Fluid_Defaults"]['THERMO_STRING']
# careful density not volume
_THERMO_TREND = request = DEFAULTS["Fluid_Defaults"]['THERMO_TREND']
_TRANS_STRING = DEFAULTS["Fluid_Defaults"]['TRANS_STRING']
_TRANS_TREND = DEFAULTS["Fluid_Defaults"]['TRANS_TREND']
_TRANS_TREND_MIX = DEFAULTS["Fluid_Defaults"]['TRANS_TREND_MIX']


_T_SURROUNDING = DEFAULTS["General"]['T_SUR']  # K
_MODEL_ARGS = {}

# order for coolprop,alle_0:[_temp, p,  h, 1/ rho, s,x,cp, mu,  lambda_s,
# prandtl, phase]"
_UNITS = 21
rp_instance = ""

if _PROPS == "REFPROP":
    DLL_SELECT = DEFAULTS["Fluid_Defaults"]['DLL_SELECT']
    try:
        rp_instance = REFPROPFunctionLibrary(os.environ['RPPREFIX'])
        # be careful pressure is in Pa!
        _UNITS = rp_instance.GETENUMdll(0, DEFAULTS["Fluid_Defaults"]['UNITS']).iEnum
    except:  # ModuleNotFoundError as errefprop:
        print("Refprop is not installed!")  # " {errefprop}")
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
        """ Set the state of a fluid in TREND. """

        self.fluid = self.fluid_to_list()
        if self.units == 21:
            self.units = "specific"

        n_compounds = len(self.fluid)
        if len(self.args["moles"]) < n_compounds:
            self.args["moles"] = list(np.zeros(n_compounds))
            self.args["moles"][0] = 1.
        if len(self.args["eos_ind"]) < n_compounds:
            self.args["eos_ind"] = list(np.ones(n_compounds))
        if self.args["mix_ind"] < 1:
            self.args["mix_ind"] = 1

        _trend_dict = {"Input": self.args["Input"],
                       'calctype': self.args['calctype'],
                       'fluids': self.fluid,
                       "moles": self.args["moles"],
                       "eos_ind": self.args["eos_ind"],
                       'mix_ind': self.args["mix_ind"],
                       'path': self.args['path'],
                       'unit': self.units,
                       'dll_path': self.args['dll_path'],
                       'libhandle': None}

        self.rp_instance = tr_fl.Fluid(*_trend_dict.values())
        err_flag = self.rp_instance.errorflag.value
        if err_flag > 0:
            print(f"fluid-Trend problem, errorflag:{err_flag}")
        return self.rp_instance

    def fluid_to_list(self):
        """
        Converts the fluid names string from Refprop to a list for TREND

        Returns
        -------
        List of strings
            the fluid names in a list.

        """
        no_blank = self.fluid.replace(" ", "")
        return no_blank.split("*")


class FluidState:
    """
    The thermodynamic state of a fluid is stored here.
    
    Which properties (T,p,h,v,s,q,...), depends on:
    carbatpy.CB_DEFAULTS["Fluid_Defaults"]["Property_Names_Short"]
    """

    def __init__(self, state, what, **kwargs):
        self.props = kwargs.get("props", _PROPS)
        self. verbose = kwargs.get("verbose", False)
        self.liq_x = kwargs.get("x", None)
        self.vap_y = kwargs.get("y", None)
        self.total_z = kwargs.get("z", None)
        
        if self.props == "REFPROP":
            self.no_val = what.count(";")+1
        elif self.props == "TREND":
            self.no_val = len (state)
        if self.props == 'REFPROP':
            names = carbatpy.CB_DEFAULTS["Fluid_Defaults"]["Property_Names_Short"]
        elif self.props == 'TREND':
            names = carbatpy.CB_DEFAULTS["Fluid_Defaults"]["Property_Names_Short_Trend"]   
        self.state = state[:self.no_val]
        for ii, key in enumerate(names.keys()):
            if ii < self.no_val:
                setattr(self,key , state[ii])

        

    def state_to_dict(self):
        """Convert the state properties to a dictionary name:value."""
        if self.props=='REFPROP':
            return_dict = dict(
                zip(_fl_properties_names[:self.no_val], self.state[:self.no_val]))
        elif self.props == 'TREND':
            return_dict = dict(
                zip(_fl_properties_names_trend[:self.no_val], self.state[:self.no_val]))
        return_dict["x"] = self.liq_x
        return_dict["y"] = self.vap_y
        return_dict["z"] = self.total_z
        return return_dict


class Fluid:
    """
    The Fluid class is used to set, get, and print states of  a fluid with a given

    model (e.g. RefProp). The compounds are set in the fluidmodel, while the
    composition is also set here. The calculated values depend also on
    carbatpy.CB_DEFAULTS["Fluid_Defaults"]["Property_Names_Short"].

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
        if composition is None:
            composition = [1.0]
        # else:
        #     self.composition = composition
        self.composition = copy.copy(composition)
        self.properties = None
        self.state_v = None
        self.option = option
        self.no_compounds = len(composition)
        self.comp_mass = np.zeros(self.no_compounds)
        self.herr = 0
        self.props = fluidmodel.props
        # BA something is wrong here (probably 2024-07-10
        self.set_composition(composition)
        self.val_dict = {}
        if self.props == "TREND":
            # important for trend mass->mole"

            self.fluidmodel.rp_instance.set_moles(self.comp_mass)
            if VERBOSE:
                print("Konversion", self.composition,
                      self.comp_mass,
                      self.composition,
                      self.fluidmodel.rp_instance.get_moles())

    def set_composition(self, composition, **kwargs):
        """
        Mole fractions are set and mass fractions are calculated.

        Sets the self.composition used in the Fluid settings and the self.comp_mass
        TREND needs the mass fractions for specific (/kg) calculations. Thus
        calc_mass_fraction() is called.

        Parameters
        ----------
        composition : list/numpy.array
            mole fractions must sum up to 1.
        kwargs : dictionary, optional.
            - verbose : boolean, optional. Generate additional printig. The default is
            False.

        Returns
        -------
        None.

        """
        verbose = kwargs.get("verbose", False)
        if verbose:
            print("set_comp", composition, self.composition, self.comp_mass)
        self.composition = composition
        if self.fluidmodel.props == "TREND":
            self.comp_mass = np.zeros((self.no_compounds))
            self.calc_mass_fraction()
            self.fluidmodel.rp_instance.set_moles(self.comp_mass)
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
        return self.comp_mass

    def set_state(self, values, given="TP", wanted=_THERMO_STRING, composition=None,
                  **kwargs):
        """
        Sets the state of a fluid and calculates the wanted properties.

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
            -dll_select : is passed to Refprop.
            dll_select is the only important one the standard value is "2dll" using the
            faster REFPROP2dll function, not calculating the composition of different
            phases. The alternative "dll" is slower but does it. Throughout it is expected that
            compoitions are mole fractions and qualities in mass/mass.
           - i_mass : Flag (0/1), optional, should not be used,  not teste.
           - i_flag : Flag (0/1), optional, should not be used,  not tested.
           - verbose : Boolean, optional, leads to additional (printing) output. The default
             value is False.
           - output : String, optional, what shall be the return value, the "state" as list
             or an instance of the "FluidState". default is "state" 



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
        self. output =kwargs.get("output", "state")

        if self.fluidmodel.props == "REFPROP":
            self._set_state_refprop(values, given, wanted, **kwargs)
        elif self.fluidmodel.props == "TREND":
            if wanted == _THERMO_STRING:
                wanted = _THERMO_TREND
            self._set_state_trend(values, given, wanted, **kwargs)
        else:
            raise NotImplementedError(
                f"Property model {self.fluidmodel.props} not implemented yet!")
        if self.output =="FluidState":
            return self.properties
        return np.array([*self.properties.state])

    def _update_composition(self, composition):
        if composition is None:  # mole fractions only!
            if self.props =='TREND':
                return self.comp_mass
            else:
                return self.composition

        self.set_composition(composition)  # important for trend mass->mole
        if VERBOSE:
            print("comp-set", composition, self.composition,
                  self.comp_mass, self.composition)
        return composition

    def _set_state_refprop(self, values, given, wanted, **kwargs):
        i_mass = kwargs.get("iMass", 0)
        i_flag = kwargs.get("iFlag", 0)  # if this is 1 most tests fail!
        dll_select = kwargs.get("dll_select", "2dll") # "2dll"
        verbose = kwargs.get("verbose", False)

        if given.count("Q") > 0:
            q_act = values[given.find("Q")]
            if 0 < q_act < 1:  # only then x and y are meaningful/needed
                dll_select = "dll"

        match dll_select:  # noqa
            case "2dll":
                i_mass = 0
                state = self.fluidmodel.rp_instance.REFPROP2dll(
                    self.fluidmodel.fluid, given, wanted,
                    self.fluidmodel.units,
                    i_flag, values[0], values[1],
                    copy.copy(self.composition)
                )
                # additional calls implemented that are used if flash calculation failed (error code 226)
                # which may happen close to saturation lines. flag 1 is single phase assumption, flag 2 is two-phase assumption
                if state.ierr == 226:
                    state = self.fluidmodel.rp_instance.REFPROP2dll(
                        self.fluidmodel.fluid, given, wanted,
                        self.fluidmodel.units,
                        2, values[0], values[1],
                        copy.copy(self.composition)
                    )
                    if verbose:
                        print("iflag 2 called")
                    
                if state.ierr == 226:
                    state = self.fluidmodel.rp_instance.REFPROP2dll(
                        self.fluidmodel.fluid, given, wanted,
                        self.fluidmodel.units,
                        1, values[0], values[1],
                        copy.copy(self.composition)
                    )
                    if verbose:
                        print("iflag 1 called")
            case "dll":
                i_mass = 1
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

        if state.ierr == 0: # for estimated mixing parameters, add: or state.ierr == -117:
            state_val = state.Output
            z_act = state.z[:self.no_compounds]
            x_act = y_act = None

            if state.q > 0 and state.q < 1:  # mole -> mass quality problem of Refprop
                # state_val[5] = state.q
                if dll_select == "dll":
                    x_act = state.x[:self.no_compounds]
                    y_act = state.y[:self.no_compounds]
                    if _UNITS == 21:  # convert back to mole fractions
                        x_act = np.array(self._rp_mole_from_mass(state.x))
                        y_act = np.array(self._rp_mole_from_mass(state.y))
                        z_act = np.array(self._rp_mole_from_mass(state.z))
            self.properties = FluidState(state_val, wanted, x=x_act, y=y_act, z=z_act)
            self.val_dict = self.properties.state_to_dict()

        else:
            self.herr = state.herr
            raise NotImplementedError(f"Property-Refprop problem: {state.herr}, {state.ierr}!")

    def _rp_mass_from_mole(self, composition):
        return self.fluidmodel.rp_instance.XMASSdll(composition).xkg[:self.no_compounds]

    def _rp_mole_from_mass(self, composition):
        return self.fluidmodel.rp_instance.XMOLEdll(composition).xmol[:self.no_compounds]

    def _set_state_trend(self, values, given, wanted, **kwargs):
        verbose = kwargs.get("verbose", False)
        self.fluidmodel.rp_instance.set_moles(self.comp_mass)
      
        if verbose:
            print("in TREND set state")

        values, given = self._adjust_trend_values(values, given)
        all_values = self.fluidmodel.rp_instance.ALLPROP(given, values[0], values[1])
        all_val_initial = copy.copy(all_values)

        if all_values["T"] > 0:  # on error it is -8888
            all_values["P"] = all_values["P"] * 1e6  # MPa
            all_values["D"] = 1 / all_values["D"]  # V (spec. volume)
            all_values = [all_values[key] for key in _THERMO_TREND]
            if len(wanted) > len(_THERMO_TREND):

                trans_dict = {}
                speed_sound = all_val_initial["WS"]
                for tr_want in wanted[len(_THERMO_TREND):]:
                    self.fluidmodel.rp_instance.set_moles(self.comp_mass)
                    self.fluidmodel.rp_instance.set_calctype(tr_want)
                    self.fluidmodel.rp_instance.set_input(given)

                    trans_dict[tr_want], err = self.fluidmodel.rp_instance.TREND_EOS(
                        *values)
                    if verbose:
                        print(tr_want, ":", trans_dict[tr_want], err)
                    if trans_dict[tr_want] < 0:
                        print(f"WARNING: Problem / NOT IMPLEMENTED IN TREND! {tr_want}")
                try:
                    trans_dict['ETA_RES'] = trans_dict['ETA_RES'] * 10**-6 #Pa s
                except:
                    pass
                try:
                    trans_dict['ETA_ECS'] = trans_dict['ETA_ECS'] * 10**-6 #Pa s
                except:
                    pass
                try:
                    trans_dict['ETA_BERLIN'] = trans_dict['ETA_BERLIN'] * 10**-6 #Pa s
                except:
                    pass
                try:
                    trans_dict['ST'] = trans_dict['ST'] / 10 ** 3 #TREND gives back 10 ** 3 N/m
                except:
                    pass
                all_values.extend(trans_dict.values())

            self.properties = FluidState(all_values, wanted, props="TREND")
            self.val_dict = self.properties.state_to_dict()
        else:
            raise NotImplementedError(
                f"property calculation in TREND failed, probably not implemented please look up the TREND error code : {all_values['T']}")

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
        match values[quality_in]:
            case 0.:
                given = "PLIQ"
            case 1.:
                given = "PVAP"
            case _:
                raise ValueError('Error: only qualities 0 or 1 for mixtures in TREND!')
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
        kwargs : dictionary optional
            This is optional and passed to REFPROP or TREND, depending on the props
            settings / chosen property model. (see set_state())
            For REFPROP the choices are:
                -

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

    def print_state(self):
        """ Print the actual state of the Fluid"""
        pr = self.properties
        flmod = self.fluidmodel
        print(f"\n{flmod.fluid}, composition: {self.composition}")

        if pr.quality >= 0:
            print(f"Quality: {pr.quality :.3f}")
        for key, value in self.val_dict.items():
            print(f"{key}    : {value}")

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
        actual_props = self.properties.state
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

    import time
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
    t0 = time.time()
    for ii in range(500):
        st0 = myFluid.set_state([T_ACT, P_ACT], "TP", composition=[.35, .65])
    t1 = time.time()
    myFluid.print_state()

    mean_temp_act = myFluid.calc_temp_mean(st0[2]+1e5)
    print(f"Mean Temperature {mean_temp_act} K")
    
    # for testing water:
    water = init_fluid("H2O", [1.0])
    T_WATER = 300.
    
    water.set_state([T_WATER,P_ACT], "TP", _TRANS_STRING)
    print(f"""\nWater at {T_WATER} K, {P_ACT/1e5} bar. 
          Cp ={water.val_dict['isobaric_heat_capacity']} ,
          Pr: {water.val_dict['Prandtl_number']}\n""")

    # value_vec = np.array([[300, 1e5], [400, 1e5], [500, 1e5]])
    # stv = myFluid.set_state_v(value_vec, "TP")

    # print(myFluid.set_state_v(value_vec, "TP"))
    # print(myFluid.set_state([300., 1.], "TQ"))

    # New simple way to get an instance of Fluid
    myFluid2 = init_fluid(FLUID, comp)

    # Refprop with mass fractions as input
    print('\n---------------- Refprop Mass fraction Input')
    FLUID = "Propane * Pentane"
    comp = [.5, .5]
    myFluid = init_fluid(FLUID, comp)
    myFluidb = init_fluid("H2O", [1])

    QUALITY = 0.5       # is interpreted by carbatpy as mol/mol to calculate state
    # but given back in string as kg/kg
    ta0 = time.time()
    for ii in range(7):
        stold =st0
        st0 = myFluid.set_state([300., QUALITY], "TQ")  # , dll_select="dll")
        sth2o = myFluidb.set_state([310,1e5], "TP")
        #print (st0-stold)
        stold = st0
    ta1 = time.time()

    print(f"Durations all: {ta1-ta0}, 2dll: {t1-t0}")
    myFluid.print_state()
    st0n = myFluid.set_state([st0[1], st0[2]], "PH", dll_select="dll")
    myFluid.print_state()

    print(f"quality prescribed: {QUALITY}")
    print(f"resulting quality from carbatpy in st0: {st0[5]}")

    print("\n------------\n")

    # Trend: --------------------------------------
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
          my_tr_fl.properties.enthalpy)
    state_tr_trans = my_tr_fl.set_state([T_ACT, P_ACT], "TP", wanted=_TRANS_TREND_MIX)
    print(f"Trans-String TREND: {state_tr_trans}")

    # shortcut to generate a trend fluid
    flt0 = carbatpy.init_fluid(FLUID, comp, props="TREND", args=my_dict)

    # saturated mixture:
    state_trend_satp = my_tr_fl.set_state([P_ACT, 0], "PQ")
    print("\nSaturated mixture, liq:\n", state_trend_satp,  my_tr_fl.properties.enthalpy)
    state_trend_satp = my_tr_fl.set_state([P_ACT, 1], "PQ")
    print("Saturated mixture, vap:\n", state_trend_satp,  my_tr_fl.properties.enthalpy)

    # some temperature dependence
    state_trend_c = my_tr_fl.set_state([230., P_ACT], "TP")

    enth = np.linspace(state_trend_c[2], state_trend[2], 25)
    all_props_act = []
    for h_act in enth:

        all_props_act.append(my_tr_fl.set_state([P_ACT, h_act], "PH"))
    all_props_act = np.array(all_props_act)

    import matplotlib.pyplot as plt
    fi, ax = plt.subplots(1)
    ax.plot(all_props_act[:, 2], all_props_act[:, 0])
    
    # return a FluidState
    my_prop = my_tr_fl.set_state([T_ACT, P_ACT], "TP",output="FluidState")
    my_prop2 = my_tr_fl.set_state([T_ACT+25, P_ACT], "TP",output="FluidState")
    print(f'Fluidstate as output: {my_prop.enthalpy, my_prop2.enthalpy}')
    my_prop = myFluid.set_state([T_ACT, P_ACT], "TP",output="FluidState")
    my_prop2 = myFluid.set_state([T_ACT+25, P_ACT], "TP",output="FluidState")
    print(f'Fluidstate as output: {my_prop.enthalpy, my_prop2.enthalpy}')
