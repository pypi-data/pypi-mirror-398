# -*- coding: utf-8 -*-
"""
Some constants for carbatpy usage are set here

* The two (!) Refprop installation directories (with dll, fluids etc.)
* he directory, where the results shall be written.

Created on Sun Nov  5 16:01:02 2023

@author: atakan
"""

import os
import copy
verbose = False
# global _T_SURROUNDING, _P_SURROUNDING, _RESULTS_DIR, _CARBATPY_BASE_DIR
_T_SURROUNDING = 288.15 # K
_P_SURROUNDING =1.013e5  # Pa
TREND = {"TREND_INSTALLED":True,
          "USE_TREND":False,
          "TREND_DLL":"",
          'TREND_PATH':"",
          'TREND_SUB_PATH': None}

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.dirname(script_dir)
# Standard directory of the installation
grandparent_dir = os.path.dirname(parent_dir)
if verbose:
    print(f"Standard Carbatpy base directory: {grandparent_dir}")

    print(f"Directory of the main source code: {script_dir}")
directory = os.getcwd()
try:
    _CARBATPY_BASE_DIR = os.environ["CARBATPY_BASE_DIR"]
    if verbose:
        print(f"You are using this custom set ('CARBATPY_BASE_DIR') base directory for carbatpy: {script_dir}")
except:
    if script_dir.count('carbatpy') >0:
        _CARBATPY_BASE_DIR = script_dir
    else:
        _CARBATPY_BASE_DIR = grandparent_dir
if verbose: print(script_dir.count('carbatpy') >0)
# The two installations of REFPROP , one for the working fluid
# and one for the secondary fluid. With only one installation, the instances
# mix up ...
os.environ['RPPREFIX'] = r'C:/Program Files (x86)/REFPROP'
os.environ['RPPREFIXs'] = r'C:/Program Files (x86)/REFPROP/secondCopyREFPROP'
if TREND["TREND_INSTALLED"]:
    try:
        TREND["TREND_DLL"] = os.environ['TREND_DLL']
        TREND["TREND_PATH"] = os.environ['TREND_PATH']     
        TREND["TREND_PATH_BASE"] = os.environ['TREND_PATH']
        

        # If a sub-path is defined, append it to TREND_PATH_BASE
        if TREND["TREND_SUB_PATH"] is not None:
            TREND["TREND_PATH"] = os.path.join(TREND["TREND_PATH_BASE"], TREND["TREND_SUB_PATH"])

    except KeyError:
        print("Trend not found! Check the environment variable TREND_DLL, TREND_PATH")
        TREND_DLL = ""
        TREND_PATH = ''
        TREND["TREND_INSTALLED"] = False

try:
    _RESULTS_DIR = os.environ['CARBATPY_RES_DIR']
except:
    try:
        _RESULTS_DIR = os.environ['TEMP']
    except:
        try:

            _RESULTS_DIR = directory + r"\\tests\\test_files"
        except Exception as no_file:
            print("Please set the envirionment variable: CARBATPY_RES_DIR !", no_file)

# Default values:-------------------------------------------------
fl_properties_names = ("Temperature",
                       "Pressure",
                       "spec_Enthalpy",
                        "spec_Volume",
                        "spec_Entropy",
                        "quality_mass",
                        "spec_internal_Energy",
                        "viscosity",
                        "thermal_conductivity",
                        "Prandtl_number",
                        "isobaric_heat_capacity",
                        "speed_of_sound",
                        "molecular_mass")

fl_pr_variable_names = {"temperature":'T',
                        'pressure': 'p',
                        'enthalpy':'h',
                        "sp_volume": "v",
                        'entropy': 's',
                        'quality': 'q',
                        'int_energy': 'u',
                        'viscosity': "eta",
                        'thermal_conductivity': "k",
                        'prandtl': "Pr",
                        "cp":"cp",
                        'speed_of_sound': "w_s",
                        'molecular_mass': "M",
                        }

fl_properties_names_trend = ("Temperature",
                       "Pressure",
                       "spec_Enthalpy",
                        "spec_Volume",
                        "spec_Entropy",
                        "quality_mass",
                        "spec_internal_Energy",
                        "viscosity",
                        "thermal_conductivity",
                        "isobaric_heat_capacity",
                        "speed_of_sound")

fl_pr_variable_names_trend = {"temperature":'T',
                        'pressure': 'p',
                        'enthalpy':'h',
                        "sp_volume": "v",
                        'entropy': 's',
                        'quality': 'q',
                        'int_energy': 'u',
                        'viscosity': "eta",
                        'thermal_conductivity': "k",
                        "cp":"cp",
                        'speed_of_sound': "w_s",
                        }

THERMO_STRING = "T;P;H;V;S;QMASS;E"
TRANS_STRING = THERMO_STRING + ";VIS;TCX;PRANDTL;CP;W;M"
THERMO_TREND = request = ["T", "P", "H", "D",
                           "S", "QEOS", "U"]  # careful density not volume
TRANS_TREND = copy.copy(THERMO_TREND)
TRANS_TREND.extend(["ETA", "TCX", "CP","WS"]) # no molecular mass

                           
TRANS_TREND_MIX = copy.copy(THERMO_TREND)
TRANS_TREND_MIX.extend(["ETA_ECS", "TCX_ECS", "CP","WS"]) # no molecular mass

CB_FLUID_DEFAULT = {"PROPS": "REFPROP",  # choice: "TREND" or "REFPROP"
                    "DLL_SELECT": "2dll",  # choice: "2dll" or "dll"
                    "UNITS": "MASS BASE SI",
                    "Property_Names":fl_properties_names,
                    "Property_Names_Short":fl_pr_variable_names,
                    "Property_Names_Trend":fl_properties_names_trend,
                    "Property_Names_Short_Trend":fl_pr_variable_names_trend,
                    "THERMO_STRING":THERMO_STRING,
                    "TRANS_STRING":TRANS_STRING ,
                    "THERMO_TREND": THERMO_TREND,
                    "TRANS_TREND": TRANS_TREND,
                    "TREND":TREND,
                    "RPPREFIX":os.environ['RPPREFIX'],
                    "TRANS_TREND_MIX": TRANS_TREND_MIX,



    }
PLOT_INFO = {"fig": None, "ax": None, "what": [2, 0], "col": ["r:", "k"],
             "label": ["compressor", "xx"], "x-shift": [0, 0]}
COMPONENT_DEFAULTS ={"Plot": PLOT_INFO,
                     "n_points": 50}
# This dictionary will be generally imported with carbatpy
CB_DEFAULTS={
    "Fluid_Defaults": CB_FLUID_DEFAULT,
    "Components":COMPONENT_DEFAULTS,
    "General":{"T_SUR":_T_SURROUNDING,
               "P_SUR": _P_SURROUNDING,
               "RES_DIR": _RESULTS_DIR,
               "CB_DIR": _CARBATPY_BASE_DIR,
               "CB_DATA":_CARBATPY_BASE_DIR+"\\data"

               }
    }