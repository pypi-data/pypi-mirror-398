# -*- coding: utf-8 -*-
"""
Class for the input of the heat pump

values are stored in a dictionarypart of carbatpy
Created on Tue Jul 23 16:48:28 2024

@author: atakan
"""

import json
import yaml

class HpVal:
    DEFAULT_DIR =cb.CB_DEFAULTS["General"]["CB_DATA"]
    DEFAULT_FILE=DEFAULT_DIR+"\\hp-input-dictvariables"
    def __init__(self, variables_dict=None):
        if variables_dict:
            for key, value in variables_dict.items():
                setattr(self, key, value)
    
    def to_dict(self):
        return {key: getattr(self, key) for key in self.__dict__}

    def save_to_json(self, file_path=DEFAULT_FILE+"_act.json"):
        with open(file_path, 'w') as json_file:
            json.dump(self.to_dict(), json_file, indent=4)

    @classmethod
    def load_from_json(cls, file_path=DEFAULT_FILE+".json"):
        with open(file_path, 'r') as json_file:
            variables_dict = json.load(json_file)
            return cls(variables_dict)

    def save_to_yaml(self, file_path=DEFAULT_FILE+"_act.yaml"):
        with open(file_path, 'w') as yaml_file:
            yaml.dump(self.to_dict(), yaml_file, default_flow_style=False)

    @classmethod
    def load_from_yaml(cls, file_path=DEFAULT_FILE+".yaml"):
        with open(file_path, 'r') as yaml_file:
            variables_dict = yaml.safe_load(yaml_file)
            return cls(variables_dict)


if __name__ == "__main__":
    # Beispielhafte Zuweisung der Variablen und Parameter
    variables_dict = {
        'FLUID': "Propane * Butane * Pentane * Hexane",
        'comp': [0.75, 0.05, 0.15, 0.05],
        'FLS': "Water",
        'FLCOLD': "Methanol",
        'ETA_S': 0.7,
        'STORAGE_T_IN': 298.15,  # Beispielwert für cb.T_SURROUNDING
        'COLD_STORAGE_T_IN': 298.15,
        'STORAGE_T_OUT': 363.0,  # 395.0
        'COLD_STORAGE_T_OUT': 250.15,
        'STORAGE_P_IN': 5e5,
        'COLD_STORAGE_P_IN': 5e5,
        'Q_DOT_MIN': 1e3,  # heat flow rate (W)
        'D_T_SUPER': 5,  # super heating of working fluid
        'D_T_MIN': 4.0  # minimum approach temperature (pinch point)
    }
    
    # Erstellen einer Instanz der Klasse HpVal
    hp_val = HpVal(variables_dict)
    
    # Speichern des Dictionaries in einer JSON-Datei
    hp_val.save_to_json('variables.json')
    
    # Einlesen des Dictionaries aus einer JSON-Datei und Erstellen einer neuen Instanz von HpVal
    hp_val_from_json = HpVal.load_from_json('variables.json')
    
    # Ausgabe, um zu prüfen, ob die Variablen korrekt zugewiesen wurden
    print("JSON:")
    print(hp_val_from_json.FLUID)
    print(hp_val_from_json.comp)
    print(hp_val_from_json.FLS)
    print(hp_val_from_json.FLCOLD)
    print(hp_val_from_json.ETA_S)
    print(hp_val_from_json.STORAGE_T_IN)
    print(hp_val_from_json.COLD_STORAGE_T_IN)
    print(hp_val_from_json.STORAGE_T_OUT)
    print(hp_val_from_json.COLD_STORAGE_T_OUT)
    print(hp_val_from_json.STORAGE_P_IN)
    print(hp_val_from_json.COLD_STORAGE_P_IN)
    print(hp_val_from_json.Q_DOT_MIN)
    print(hp_val_from_json.D_T_SUPER)
    print(hp_val_from_json.D_T_MIN)
    
    # Speichern des Dictionaries in einer YAML-Datei
    hp_val.save_to_yaml('variables.yaml')
    
    # Einlesen des Dictionaries aus einer YAML-Datei und Erstellen einer neuen Instanz von HpVal
    hp_val_from_yaml = HpVal.load_from_yaml('variables.yaml')
    
    # Ausgabe, um zu prüfen, ob die Variablen korrekt zugewiesen wurden
    print("\nYAML:")
    print(hp_val_from_yaml.FLUID)
    print(hp_val_from_yaml.comp)
    print(hp_val_from_yaml.FLS)
    print(hp_val_from_yaml.FLCOLD)
    print(hp_val_from_yaml.ETA_S)
    print(hp_val_from_yaml.STORAGE_T_IN)
    print(hp_val_from_yaml.COLD_STORAGE_T_IN)
    print(hp_val_from_yaml.STORAGE_T_OUT)
    print(hp_val_from_yaml.COLD_STORAGE_T_OUT)
    print(hp_val_from_yaml.STORAGE_P_IN)
    print(hp_val_from_yaml.COLD_STORAGE_P_IN)
    print(hp_val_from_yaml.Q_DOT_MIN)
    print(hp_val_from_yaml.D_T_SUPER)
    print(hp_val_from_yaml.D_T_MIN)
