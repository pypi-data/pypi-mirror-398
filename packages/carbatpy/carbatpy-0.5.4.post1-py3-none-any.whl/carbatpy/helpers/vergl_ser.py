# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 13:26:46 2024

@author: atakan
"""

import json
import numpy as np
import yaml
import os

class Serializable:
    default_path = ''
    default_filename = 'default.json'
    
    @property
    def all(self):
        return {key: value for key, value in self.__dict__.items() if key != 'all'}

    def _is_serializable(self, value):
        try:
            json.dumps(value)
            return True
        except (TypeError, OverflowError):
            return False

    def _to_serializable(self, value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, (np.float64, np.int64)):
            return value.item()
        elif hasattr(value, 'to_dict'):
            return value.to_dict()
        elif isinstance(value, dict):
            return {k: self._to_serializable(v) for k, v in value.items() if self._is_serializable(v)}
        elif isinstance(value, list):
            return [self._to_serializable(item) for item in value if self._is_serializable(item)]
        elif isinstance(value, (int, float, str, bool)):
            return value
        else:
            return str(value)

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            result[key] = self._to_serializable(value)
        return result

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
                setattr(instance, key, np.array(value))
            elif isinstance(value, dict):
                if 'optimize' in value or 'setting' in value:  # Hier kannst du die spezifischen Schlüssel überprüfen
                    setattr(instance, key, value)
                else:
                    setattr(instance, key, cls.from_dict(value))
            else:
                setattr(instance, key, value)
        return instance

    def save_to_file(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(self.default_path, self.default_filename)
        try:
            data = self.to_dict()
            if file_path.endswith('.json'):
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'w') as file:
                    yaml.dump(data, file, default_flow_style=False)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml/.yml")
        except Exception as e:
            print(f"Error saving to file: {e}")

    @classmethod
    def load_from_file(cls, file_path=None):
        if file_path is None:
            file_path = os.path.join(cls.default_path, cls.default_filename)
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as file:
                    data = json.load(file)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'r') as file:
                    data = yaml.load(file, Loader=yaml.SafeLoader)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml/.yml")

            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading from file: {e}")
            return None


# Beisp
class ExampleClass(Serializable):
    default_path = r'C:\Users\atakan\sciebo\results'
    default_filename = 'example_class.json'

    def __init__(self):
        self.D_T_MIN = 4.0
        self.D_T_SUPER = 5
        self.ETA_S_C = 0.7
        self.FLUID_COLD = 'Methanol'
        self.FLUID_STORAGE = 'Water'
        self.FLUID_WORKING = 'Propane * Butane * Pentane * Hexane'
        self.P_IN_STORAGE_COLD = 500000.0
        self.P_IN_STORAGE_HOT = 500000.0
        self.P_WORKING = {'optimize': 'p and x',
                          'setting': 'fixed-p',
                          'p_low': np.float64(88596.5138086614),
                          'p_high': np.float64(1468265.9209155128)}
        self.Q_DOT_MIN = 1000.0
        self.T_IN_STORAGE_COLD = 288.15
        self.T_IN_STORAGE_HOT = 288.15
        self.T_OUT_STORAGE_COLD = 250.15
        self.T_OUT_STORAGE_HOT = 363.0
        self.fluids_all = [['WORKING', 'Propane * Butane * Pentane * Hexane', np.array([0.675, 0.0515, 0.2735])],
                           ['STORAGE_HOT', 'Water', [1.0]],
                           ['STORAGE_COLD', 'Methanol', [1.0]]]
        self.p_low = np.float64(88596.5138086614)
        self.p_high = np.float64(1468265.9209155128)
        self.h_h_out_w = np.float64(143340.64571347312)
        self.h_l_out_w = np.float64(498179.4484371684)
        self.h_h_out_sec = np.float64(376741.38712295156)
        self.h_l_out_cold = np.float64(-220917.46629775176)
        self.T_hh = 363.0

# Erstellen einer Instanz und Speichern in einer Datei
example = ExampleClass()
example.save_to_file()

# Laden aus der Datei
loaded_example = ExampleClass.load_from_file()
print(loaded_example.to_dict())



    