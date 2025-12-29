# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 16:43:54 2024

@author: atakan
"""

import json
import yaml
import carbatpy as cb
res_dir =cb._RESULTS_DIR+'\\hp-input-dict'

# Zuweisung der Variablen und Parameter
FLUID = "Propane * Butane * Pentane * Hexane"
comp = [0.75, 0.05, 0.15, 0.05]
# comp = [0.4, 0.3, 0.3, 0.0]  # [0.164, 0.3330, 0.50300, 0.0]

FLS = "Water"
FLCOLD = "Methanol"
ETA_S_ = 0.7
_STORAGE_T_IN_ = 298.15  # Beispielwert für cb._T_SURROUNDING
_COLD_STORAGE_T_IN_ = _STORAGE_T_IN_
_STORAGE_T_OUT_ = 363.0  # 395.0
_COLD_STORAGE_T_OUT_ = 250.15
_STORAGE_P_IN_ = 5e5
_COLD_STORAGE_P_IN_ = 5e5
_Q_DOT_MIN_ = 1e3  # heat flow rate (W)
_D_T_SUPER_ = 5  # super heating of working fluid
_D_T_MIN_ = 4.0  # minimum approach temperature (pinch point)

# Speichern der Variablen und Parameter in einem Dictionary
variables_dict = {
    'FLUID': FLUID,
    'comp': comp,
    'FLS': FLS,
    'FLCOLD': FLCOLD,
    'ETA_S_': ETA_S_,
    '_STORAGE_T_IN_': _STORAGE_T_IN_,
    '_COLD_STORAGE_T_IN_': _COLD_STORAGE_T_IN_,
    '_STORAGE_T_OUT_': _STORAGE_T_OUT_,
    '_COLD_STORAGE_T_OUT_': _COLD_STORAGE_T_OUT_,
    '_STORAGE_P_IN_': _STORAGE_P_IN_,
    '_COLD_STORAGE_P_IN_': _COLD_STORAGE_P_IN_,
    '_Q_DOT_MIN_': _Q_DOT_MIN_,
    '_D_T_SUPER_': _D_T_SUPER_,
    '_D_T_MIN_': _D_T_MIN_,
}

# Funktion zum Wiederzuweisen der Variablen aus dem Dictionary
def assign_variables_from_dict(variables_dict):
    global FLUID, comp, FLS, FLCOLD, ETA_S_, _STORAGE_T_IN_
    global _COLD_STORAGE_T_IN_, _STORAGE_T_OUT_, _COLD_STORAGE_T_OUT_
    global _STORAGE_P_IN_, _COLD_STORAGE_P_IN_, _Q_DOT_MIN_, _D_T_SUPER_, _D_T_MIN_
    
    FLUID = variables_dict['FLUID']
    comp = variables_dict['comp']
    FLS = variables_dict['FLS']
    FLCOLD = variables_dict['FLCOLD']
    ETA_S_ = variables_dict['ETA_S_']
    _STORAGE_T_IN_ = variables_dict['_STORAGE_T_IN_']
    _COLD_STORAGE_T_IN_ = variables_dict['_COLD_STORAGE_T_IN_']
    _STORAGE_T_OUT_ = variables_dict['_STORAGE_T_OUT_']
    _COLD_STORAGE_T_OUT_ = variables_dict['_COLD_STORAGE_T_OUT_']
    _STORAGE_P_IN_ = variables_dict['_STORAGE_P_IN_']
    _COLD_STORAGE_P_IN_ = variables_dict['_COLD_STORAGE_P_IN_']
    _Q_DOT_MIN_ = variables_dict['_Q_DOT_MIN_']
    _D_T_SUPER_ = variables_dict['_D_T_SUPER_']
    _D_T_MIN_ = variables_dict['_D_T_MIN_']

# Speichern des Dictionaries in einer JSON-Datei
with open(res_dir+'variables.json', 'w') as json_file:
    json.dump(variables_dict, json_file, indent=4)

# Einlesen des Dictionaries aus einer JSON-Datei
with open(res_dir+'variables.json', 'r') as json_file:
    variables_dict = json.load(json_file)

# Variablen aus dem Dictionary zuweisen
assign_variables_from_dict(variables_dict)

# Ausgabe, um zu prüfen, ob die Variablen korrekt zugewiesen wurden
print("JSON:")
print(FLUID)
print(comp)
print(FLS)
print(FLCOLD)
print(ETA_S_)
print(_STORAGE_T_IN_)
print(_COLD_STORAGE_T_IN_)
print(_STORAGE_T_OUT_)
print(_COLD_STORAGE_T_OUT_)
print(_STORAGE_P_IN_)
print(_COLD_STORAGE_P_IN_)
print(_Q_DOT_MIN_)
print(_D_T_SUPER_)
print(_D_T_MIN_)

# Speichern des Dictionaries in einer YAML-Datei
with open(res_dir+'variables.yaml', 'w') as yaml_file:
    yaml.dump(variables_dict, yaml_file, default_flow_style=False)

# Einlesen des Dictionaries aus einer YAML-Datei
with open(res_dir+'variables.yaml', 'r') as yaml_file:
    variables_dict = yaml.safe_load(yaml_file)

# Variablen aus dem Dictionary zuweisen
assign_variables_from_dict(variables_dict)

# Ausgabe, um zu prüfen, ob die Variablen korrekt zugewiesen wurden
print("\nYAML:")
print(FLUID)
print(comp)
print(FLS)
print(FLCOLD)
print(ETA_S_)
print(_STORAGE_T_IN_)
print(_COLD_STORAGE_T_IN_)
print(_STORAGE_T_OUT_)
print(_COLD_STORAGE_T_OUT_)
print(_STORAGE_P_IN_)
print(_COLD_STORAGE_P_IN_)
print(_Q_DOT_MIN_)
print(_D_T_SUPER_)
print(_D_T_MIN_)

