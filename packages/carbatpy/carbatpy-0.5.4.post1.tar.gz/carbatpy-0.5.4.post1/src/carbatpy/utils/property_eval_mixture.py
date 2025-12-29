# -*- coding: utf-8 -*-
"""

A script to evaluate mixtures, in order to find some with vapor pressures
in some limits at given temperatures, together with the temperature glide.
The results are stored as figure, as csv and in a json-file(Input); all in the
given directory.


The csv output file structure is as follows:

* number of calculation
* the four mole fractions, species names are in the title
* index l: the properties for saturated vapor at the given low temperature
* index sup: the poperties at superheating at pressure p_l for a prescribed superheating
* index h: the properties for saturated vapor at the given high temperature
* index is: the properties for the isentropic state (sup ->p_h) at the given low temperature
* index is80: the properties for the isentropic effic. of 80 % (sup ->p_h) at the given low temperature
* index dew: the properties for the saturated liquid at p_h
* index mid: the properties at the mean enthalpy between q=0 and q=1 at p_h
* index thr: the properties for the isenthalpic throtteling from saturated liquid to p_l
* index hplT: the properties at T_l and p_h
* index thrlow: the properties for the isenthalpic throtteling from hplt ->p_l
* index bol: the properties for saturated liquid at the low pressure p_l
* p_ratio: the pressure ratio
* T_glide_h: the temperature glide at high pressure
* dv/v'': (ca.) the mean change in volume along throtteling relative to the specific volume of the vapor, this is a measure of how much work is 'lost' along throtteling
* dv/v''-b: similar volume ratio after subcooling to thrlow, answer the question: will subcooling reduce losses (strongly)?
* COP_is: What is the predicted COP for isentropic compression (losses along throtteling are seen here)

For each indexed state : T,p,h,v,s,q,u in SI units(mass base) are listed.


part of carbatpy

Created on Thu Oct 19 14:11:14 2023

@author: atakan
"""

import os
import json
import itertools
import matplotlib.pyplot as plt
import seaborn as sbn
import pandas as pd
import numpy as np
import carbatpy as cb


def mixture_search(fluids_all, temp_both, p_both, res_dir, d_temp_superheating=5,
                   resolution=21, temp_limit=False, **kwargs):
    """
    Mixtures are evaluated/screened to find mixtures with a given temperature
    glide in a certain pressure range. For all possible mixture compositions
    first the saturated vapor pressure at the given low temperature and composition
    is evaluated, if it is in the allowed regime, the saturated vapor pressure
    (p_h) of the mixture at the high temperature is evaluated.
    If this is below the allowed high
    pressure, the saturated liquid temperature at this p_h is evaluated and the
    temperature difference is taken as temperature glide. The pressure ratio is
    plotted as a function of temperature glide.
    The plot, the states (as csv-file) and the input parameters (as .json-file)
    are stored.
    in the csv-File first the mole fractions are given followed by the
    properties of the low temperature sat.vapor, after superheating,
    for thehigh temperature sat. vapor, the isentropic state after compression,
    high pressure sat.liquid, low pressuer isenthalpic (throtteling) state to
    the high pressure sat. liquid, and the low pressure saturated liquis state.
    For each of them: T,p,h,v,s,q,u in SI units(mass base)

    Parameters
    ----------
    fluids_all : list of strings
        up to 4 fluid names of the mixture, as defined in the fluid model
        (REFPROP).
    temp_both : List of two floats
        the minimum (at low pressure) and the maximum (at high pressure)
        saturated vapor temperature (both dew points) in K.
    p_both : List of two floats
        allowed min and max pressure in Pa.
    res_dir : string
        Directory name, where the results are stored.
    d_temp_superheating : float. optional
        super heating temperature in K. The default is 5.
    resolution : integer, optional
        inverse is the interval for the mole fraction screening (21 means every
        0.05 a value is calculated). The default is 21.
    temp_limit : Boolean, optional
        selects only values, where the temperature of the saturated liquid at
        high pressure is above temp_both[0]. The default is False.
    kwargs : dict
        is not implemented yet, but can be used later to select another fluid
        model, instead of REFPROP.

    Returns
    -------
    None.

    """
    # dir_name = r"C:\Users\atakan\sciebo\results\optimal_hp_fluid"
    eff_isentropic = 0.8  # isentropic efficiency, compressor
    all_results = {}
    exception_messages = []
    all_results["warn"] = 0
    if len(kwargs) > 0:
        print(f"These arguments are not implemented yet{kwargs}")
        all_results["warn"] = 1
    dir_name = res_dir

    plt.style.use('seaborn-v0_8-poster')  # 'seaborn-v0_8-poster')
    # fluids_all = ["Ethane", "Propane", "Pentane", "CO2"]
    fluid_mixture = "*".join(fluids_all)
    # fluid_mixture = "Dimethylether * Butane * Pentane * Hexane" #  "Propane * Butane * Pentane * Hexane"
    names = ["x_" + s for s in fluids_all]

    fn_end = "".join([s[:3] for s in fluids_all])
    fname = cb.helpers.file_copy.copy_script_add_date(
        fn_end, __file__, dir_name)
    # fname = date + fn_end
    comp = [.5, 0., 0.5, 0.0]  # , 0.0]

    flm = cb.fprop.FluidModel(fluid_mixture)
    my_fluid = cb.fprop.Fluid(flm, comp)
    temp_low, temp_high = temp_both
    p_low, p_high = p_both
    x_i_range = np.linspace(0, 1, resolution)
    results = []
    sound_speeds = []
    lin_t_deviations_all =[]

    n_species = len(fluids_all)

    variables_dict = {"File_name": fname,
                      "Dir_name": dir_name,
                      "Fluid": fluid_mixture,
                      "T_low": temp_low,
                      "T_high": temp_high,
                      "d_temp_superheating": d_temp_superheating,
                      "p_low": p_low,
                      "p_high": p_high,
                      "eta_is80": eff_isentropic,
                      "what": "T_sat_l, T_sat_h, T_super, T_is,T_is80, T_throt,Tsat_l_high"
                      }

    # Dateipfad, in dem die JSON-Datei gespeichert wird
    json_file_path = fname+"_variablen.json"

    # Speichern des Dictionaries in einer JSON-Datei
    with open(json_file_path, 'w', encoding="utf-8") as json_file:
        json.dump(variables_dict, json_file)

    print(f"Variablen wurden in '{json_file_path}' gespeichert.")
    mole_fractions = np.zeros((n_species))

    for positions in itertools.product(range(len(x_i_range)), repeat=n_species-1):
        # positions ist ein Tupel, das die ausgewählten Positionen enthält
        actual_x = np.array([x_i_range[i] for i in positions])
        if actual_x.sum() <= 1:
            mole_fractions[:n_species-1] = actual_x
            mole_fractions[n_species-1] = 1 - actual_x.sum()
            my_fluid.set_composition(mole_fractions)

            try:
                state_low = my_fluid.set_state(
                    [temp_low - d_temp_superheating, 1.], "TQ")  # find low pressure
                state_sup = my_fluid.set_state([state_low[1], temp_low],
                                               "PT", cb.fprop._TRANS_STRING)  # super heated state at low pressure
                s_speed = state_sup[-1]  # needed for the machines
                state_sup = state_sup[:7]
                if (state_low[1] > p_low) and (state_low[1] < p_high):
                    state_low_boil = my_fluid.set_state([state_low[1], 0],
                                                        "PQ")  # saturated liquid at low pressure
                    state_high = my_fluid.set_state(
                        [temp_high, 1.], "TQ")  # find high pressure, sat. vapor

                    if (state_high[1] < p_high and state_high[1] > p_low):

                        state_is = my_fluid.set_state(
                            [state_high[1], state_sup[4]], "PS")  # isentropic compression
                        work_is = state_is[2] - state_sup[2]
                        work_80 = work_is / eff_isentropic
                        # state after compression with eff_isentropic
                        state_is80 = my_fluid.set_state(
                            [state_high[1], state_sup[2] + work_80], "PH")

                        # saturated liquid at high pressure
                        state_dew = my_fluid.set_state(
                            [state_high[1], 0], "PQ")

                        # check the deviation from linearity at high p
                        state_average = (state_high + state_dew) / 2
                        state_mid = my_fluid.set_state(
                            [state_high[1], state_average[2]], "PH")
                        lin_temp_deviation = (state_mid[0] - state_average[0])

                        if temp_limit and state_dew[0] > temp_low:
                            state_throttle = my_fluid.set_state([state_dew[2],
                                                                 state_low[1]], "HP")  # throtteling the liquid to low pressure
                            state_high_p_low__temp = my_fluid.set_state(
                                [state_high[1], temp_low], "PT")  # high pressure cooled to low_t
                            state_throttle_low = my_fluid.set_state([state_high_p_low__temp[2],
                                                                    state_low[1]], "HP")
                            results.append(np.array([*mole_fractions, *state_low,
                                                     *state_sup,
                                                     *state_high,
                                                     *state_is,
                                                     *state_is80,
                                                     *state_dew,
                                                     *state_mid,
                                                     *state_throttle,
                                                     *state_high_p_low__temp,
                                                     *state_throttle_low,
                                                     *state_low_boil]))
                            sound_speeds.append(s_speed)
                            lin_t_deviations_all.append(lin_temp_deviation)
            except Exception as ex_message:
                exception_messages.append(ex_message)

    property_names = cb.fprop._fl_properties_names[:7]
    results = np.array(results)
    names = [*names, *[n+"_l" for n in property_names],
             *[n+"_sup" for n in property_names],
             *[n+"_h" for n in property_names],
             *[n+"_is" for n in property_names],
             *[n+"_is80" for n in property_names],
             *[n+"_dew" for n in property_names],
             *[n+"_mid" for n in property_names],
             *[n+"_thr" for n in property_names],
             *[n+"_hplt" for n in property_names],
             *[n+"_thrlow" for n in property_names],
             *[n+"_bol" for n in property_names]
             ]

    dframe = pd.DataFrame(data=results, columns=names)
    dframe.to_csv(fname+".csv")
    add_data={}
    add_data["speed_of_sound_sup"] = sound_speeds
    add_data["p_difference"] = dframe["Pressure_h"] - dframe["Pressure_l"]
    add_data["$p_h/p_l$"] = dframe["Pressure_h"] / dframe["Pressure_l"]
    add_data['$T_{glide,h}$'] = dframe["Temperature_h"] - dframe["Temperature_dew"]
    add_data["delta_T_mid"] = lin_t_deviations_all
    add_data["dv_v''"] = 1 - (dframe[property_names[3]+"_thr"]
                            + dframe[property_names[3]+"_dew"]) / \
        (dframe[property_names[3]+"_is"] + dframe[property_names[3]+"_sup"])
    if temp_limit:
        add_data["dv_v''"] = 1 - (dframe[property_names[3]+"_thr"]
                                + dframe[property_names[3]+"_dew"]) / \
            (dframe[property_names[3]+"_is"] +
             dframe[property_names[3]+"_sup"])
        add_data["dv_v''_b"] = 1 - (dframe[property_names[3]+"_thrlow"]  # does it help to subcool?
                                  + dframe[property_names[3]+"_hplt"]) / \
            (dframe[property_names[3]+"_is"] + \
             dframe[property_names[3]+"_sup"])
        add_data["COP_is"] = (dframe[property_names[2]+"_is"]
                            - dframe[property_names[2]+"_dew"]) /\
            ((dframe[property_names[2]+"_is"]-dframe[property_names[2]+"_sup"]))
        add_data["COP_is80"] = (dframe[property_names[2]+"_is80"]
                              - dframe[property_names[2]+"_dew"]) /\
            ((dframe[property_names[2]+"_is80"] -
             dframe[property_names[2]+"_sup"]))
    add_data = pd.DataFrame.from_dict(add_data)
    all_data= pd.concat([dframe, add_data], axis=1)
    
    all_data.to_csv(fname+".csv")

    # Plot
    figure, axes = plt.subplots(
        figsize=(10, 10), layout="constrained", nrows=1, ncols=1)
    fff = sbn.scatterplot(x="$T_{glide,h}$", y="$p_h/p_l$",
                          hue=names[0], size=names[1],
                          style=names[2], data=all_data.round(3), ax=axes)
    sbn.move_legend(fff, "upper left", bbox_to_anchor=(1, 1))
    axes.set_title(f"Mix: {fluids_all},{temp_low:.1f}, { d_temp_superheating:.1f}, {temp_high:.1f}")
    figure.savefig(fname+".png")

    all_results["exception_messages"] = exception_messages
    all_results["results_DataFrame"] = all_data
    return all_results


def eval_is_eff_roskosch(data, file_out):
    """
    Evalutes the data in the combined dataFrame with the initial fluid screening

    and the output of the Roskosch compressor model (h_aus, s_aus, h_e) for
    exactly the states
    calculated along the screening. The column names are quite special and
    one has to know that the Roskosch model calculates in kJ, while carbatpy
    uses SI units (J). With the output enthalpy of the Roskosch model, the
    **COP_comp** is calculated. Using the enthalpies and entropies along the
    isobaric heat ransfer, mean temperatures are calculated.Here are again two
    cases

    .. line-block::
        a) for throttling at quality=0 
        b) throttling after subcooling to     T_low (names: *_lowT*). 

    With these mean
    temperatures, the COPs for two reversible cases are calculated: for the
    isentropic efficieciecy of 80% *COP_rev80* and for the Roskosch 'real'
    case *COP_rev_r*. Finally, the (pseudo-)real COP is compared to the
    reversible COP, giving a second law efficiency *eff_sec_law_r* for the
    Roskosch efficiencies and *eff_sec_law_80* for the fixed 80% efficiency,
    which include the
    compressor and the throttling, but **no heat transfer**!

    The Roskosch piston compressor model is described here:
    http://dx.doi.org/10.1016/j.ijrefrig.2017.08.011

    Is part of carbatpy.

    Parameters
    ----------
    data : pandas.dataFrame
        as calculated by combining the fluid screening dataFrame with the
        ouput of the Roskosch model (as dataFrame).
    file_out : string
        name of the file (incl. directory) where the resulting dataFrame shall
        be stored.

    Returns
    -------
    data : pandas.dataFrame
        input expanded by the results.

    """

    # mean low T, first with throttling at x=0, then with subcooling to T_low
    # index name for the latter _lowT
    new_data ={}
    new_data["T_mean_low"] = (data['spec_Enthalpy_sup'] - data['spec_Enthalpy_thr']
                          ) / (data['spec_Entropy_sup'] - data['spec_Entropy_thr'])
    new_data["T_mean_low_lowT"] = (data['spec_Enthalpy_sup'] - data['spec_Enthalpy_thrlow']
                               ) / (data['spec_Entropy_sup'] - data['spec_Entropy_thrlow'])

    try:  # if the Roskosch-model data are in the dataFrame
        new_data["COP_comp"] = (data["h_aus"] * 1000 - data['spec_Enthalpy_dew']) /\
            ((data["h_aus"] - data["h_e"]) * 1000)
        new_data["T_mean_high_is_r"] = (
            data['h_aus'] * 1000 - data['spec_Enthalpy_dew'])/(data['s_aus'] - data['spec_Entropy_dew'])
        new_data["COP_rev_r"] = data["T_mean_high_is_r"] / (data["T_mean_high_is_r"]
                                                        - new_data["T_mean_low"])
        new_data["COP_rev_r_lowT"] = data["T_mean_high_is_r"] / (data["T_mean_high_is_r"]
                                                             - new_data["T_mean_low_lowT"])
        new_data["eff_sec_law_r"] = data["COP_comp"] / data["COP_rev_r"]
        new_data["eff_sec_law_r_lowT"] = data["COP_comp"] / data["COP_rev_r_lowT"]
    except:
        pass

    # values for isentropic efficiency of 80% and throttling at a quality of 0
    new_data["T_mean_high_is80"] = (data['spec_Enthalpy_is80'] - data['spec_Enthalpy_dew']) \
        / (data['spec_Entropy_is80'] - data['spec_Entropy_dew'])
    new_data["COP_rev80"] = new_data["T_mean_high_is80"] / (new_data["T_mean_high_is80"]
                                                    - new_data["T_mean_low"])
    new_data["eff_sec_law_80"] = data["COP_is80"] / new_data["COP_rev80"]

    # values for isentropic efficiency of 80% and throttling at the low T and high p
    new_data["T_mean_high_is80_lowT"] = (data['spec_Enthalpy_is80'] - data['spec_Enthalpy_hplt']) \
        / (data['spec_Entropy_is80'] - data['spec_Entropy_hplt'])
    new_data["COP_rev80_lowT"] = new_data["T_mean_high_is80"] / (new_data["T_mean_high_is80"]
                                                         - new_data["T_mean_low_lowT"])
    new_data["eff_sec_law_80_lowT"] = data["COP_is80"] / new_data["COP_rev80_lowT"]
    new_data = pd.DataFrame.from_dict(new_data)
    all_data= pd.concat([data, new_data], axis=1)
    all_data.to_csv(file_out)
    return all_data


def get_fluid(data):
    """
    find the fluids used in the screening

    Parameters
    ----------
    data : pandas.dataFrame
        dataFrame from fluid screening with mole fractions. In the column names
        the names of the fluids are found.

    Returns
    -------
    fluids : list of strings
        names of the fluids.
    fluid_col : list of strings
        List with the column names (includes a sarting"x_".
    fluid_str : string
        Fluid composition string as accepted by RefProp.

    """
    fluids = []
    fluid_col = []
    col_names = data.columns
    for name in col_names:
        if name.find("x_") > -1:
            if name not in fluid_col:  # no doubles
                fluids.append(name[2:])
                fluid_col.append(name)
    fluid_str = "*".join(fluids)
    return fluids, fluid_col, fluid_str


def combine(filenames, filename_out="automatic"):
    """
    Combine two data frames out of two or more files with same number of lines

    and fitting to each other. Can be used, when after fluid screening
    machine efficienceies, costs,
    etc. are calculated as post-processing. Can help in evaluation and
    plotting.

    Parameters
    ----------
    filenames : list of strings
        all filenames (incl. directories), to be read.
    filename_out : string, optional
        Where to store the result. The default is "automatic". Then the first
        filename isxpanded vy "-combined".

    Raises
    ------
    ValueError
        If tgere is a problem with the files.

    Returns
    -------
    combined : pandas.dataFrame
        the combined dataFrame.

    """
    all_frames = []
    if filename_out == "automatic":
        fname_new = filenames[0].split(".")
        filename_out = fname_new[0]+"-combined0." + fname_new[1]
    try:
        for which in filenames:
            all_frames.append(pd.read_csv(which))

    except Exception as excep:
        text = f"{which} vs. {os.getcwd()}, {excep}"
        raise ValueError(text) from excep
    combined = pd.concat(all_frames, axis=1)
    combined.to_csv(filename_out)
    return combined



def data_plot(filename, what, filename_out="automatic", fig_title=""):
    """
    Plotting a dataframe from a file using a dictionary with the keys

    being the plotted parameters "x", "y", "hue" etc. and storing it to
    a file.

    Parameters
    ----------
    filename : string
        csv-file with the data-frame to be imported.
    what : dictionary
        keys "y","x","hue", "style", size etc. values must be some column names. .
    filename_out : string, optional
        where to store the plot, including directory. The default is "automatic".
    fig_title : string, optional
        Title of the figure to be plotted, default is "".

    Returns
    -------
    bool
        success?

    """
    try:
        dframe = pd.read_csv(filename)

        set(what).issubset(set(dframe.columns))
    except Exception as excep:
        print(f"{what} not in columns!\n{excep}")
        return False
    # Plot
    figure, axes = plt.subplots(
        figsize=(10, 10), layout="constrained", nrows=1, ncols=1)
    fff = sbn.scatterplot(x=what["x"], y=what["y"],
                          hue=what["hue"], size=what["size"],
                          style=what["style"], data=dframe.round(3), ax=axes)
    sbn.move_legend(fff, "upper left", bbox_to_anchor=(1, 1))
    axes.set_title(fig_title)
    if filename_out == "automatic":
        filename_out = filename.split(".")[0] + "-plot2.png"
    figure.savefig(filename_out)
    return True

def plot_cycle(filename, dataset):
    try:
        dframe = pd.read_csv(filename)

        
    except Exception as excep:
        print(f"Problem: {excep}")
        return False
    
    
def get_cycle_points(data, index):
    
    indices =range(7)
    

    sup_names = [ "_l" ,
             "_sup" ,
             "_h" ,
             "_is" ,
             "_is80" ,
             "_dew" ,
             "_mid" ,
             "_thr" ,
             "_hplt" ,
             "_thrlow" ,
             "_bol" 
             ]
    n_points = len(sup_names)
    points =np.zeros((len(indices),n_points))
    for outer, variable in enumerate(indices):
        property_name = cb.fprop._fl_properties_names[variable]
        names = [property_name + sup for sup in sup_names]
        
        
        points[outer,:] = data.loc[index, names]
    return points

if __name__ == "__main__":
    FLUIDS_ACTUAL = ["Propane", "Isobutane", "Pentane", "Ethane"]  # ,"Butane"]  # ["DME", "Ethane", "Butane","CO2"]
    TEMP_LOW = 288.00
    TEMP_HIGH = 368.00
    PRESSURE_LOW = 10E4
    PRESSURE_HIGH = 22E5
    DIRECTORY_NAME = cb._RESULTS_DIR + r"\optimal_hp_fluid\fluid_select_restricted"
    TEMPERATURE_LIMIT = True
    warn = mixture_search(FLUIDS_ACTUAL, [TEMP_LOW, TEMP_HIGH],
                          [PRESSURE_LOW, PRESSURE_HIGH],
                          DIRECTORY_NAME, resolution=21,
                          temp_limit=TEMPERATURE_LIMIT)
    #####################################################
    COMPRESSOR_MODELL = False
    if COMPRESSOR_MODELL:
    
        directory = cb._CARBATPY_BASE_DIR
        directory += "\\tests\\test_files\\"
    
        filename1 = directory + r"test_data_ProEthPenBut\2024-02-06-16-51-ProEthPenBut.csv"
        filename2 = directory + \
            r"test_data_ProEthPenBut\2024-02-06-16-51-ProEthPenBut-compressor-Roskosch.csv"
        combined_data = cb.utils.property_eval_mixture.combine([filename1,
                                                                filename2],
                                                               filename_out="automatic")
        ##############################################
        what_act = {"x": 'spec_Volume_sup', "y": 'COP_is80', "hue": 'T_glide_h',
                    "size": 'p_ratio', 'style': 'Temperature_hplt'}
        SUCCESS = data_plot(filename1, what_act)
    
        ############################################
        fluids_act, fluid_col_act, fluid_str_act = get_fluid(combined_data)
    
        #########################################
        evaluated_data = eval_is_eff_roskosch(combined_data,
                                              directory+'evaluated.csv')
