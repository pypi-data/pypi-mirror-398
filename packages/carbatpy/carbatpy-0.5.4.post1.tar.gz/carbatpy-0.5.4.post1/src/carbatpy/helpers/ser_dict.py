# -*- coding: utf-8 -*-
"""
Serialisation and storing dictionaries

Some German explanations from ChatGPT:

Um die Funktionalität für die Serialisierung und Deserialisierung sowie die Dateioperationen in mehreren Klassen zu verwenden, kannst du eine Basisklasse erstellen, die diese Methoden enthält. Andere Klassen können dann von dieser Basisklasse erben. Dadurch musst du den Code nicht in jede Klasse kopieren, sondern kannst die Methoden einfach durch Vererbung wiederverwenden.

Hier ist ein Beispiel, wie du dies machen kannst:
Basisklasse erstellen

Erklärung

    Basisklasse Serializable:
        Diese Klasse enthält alle Methoden und Eigenschaften, die für die Serialisierung, Deserialisierung und Dateioperationen erforderlich sind.
        Andere Klassen können einfach von dieser Basisklasse erben, um diese Funktionalitäten zu nutzen.

    Erben von Serializable:
        Die Klassen AnotherClass und YetAnotherClass erben von Serializable.
        Sie erhalten dadurch automatisch Zugriff auf alle Methoden und Eigenschaften von Serializable.

    Verwendung:
        Instanzen der abgeleiteten Klassen können erstellt, in JSON- oder YAML-Dateien gespeichert und wieder aus diesen Dateien geladen werden, ohne dass der Code für diese Funktionalitäten in jeder Klasse wiederholt werden muss.

Durch die Verwendung einer Basisklasse und Vererbung wird dein Code modularer, wiederverwendbarer und leichter zu warten.


Bei der Basisklasse steht explizit "AnotherClass", das muss doch ein Fehler sein, oder?
ChatGPT

Du hast recht, das war ein Fehler. Die Referenz auf AnotherClass in der Methode from_dict sollte generisch sein, damit sie für jede abgeleitete Klasse funktioniert. Hier ist die korrigierte Version:
Erklärung der Änderungen

    Generische Deserialisierung:
        In der Methode from_dict wird die Deserialisierung nun allgemein gehalten. Wenn ein Dictionary ein 'value'-Schlüssel hat, wird angenommen, dass es sich um eine spezielle Struktur handelt, die ebenfalls deserialisiert werden muss. Hier kann die Logik angepasst werden, um spezifische Klassen zu unterstützen.

    Serializable.from_dict:
        Um eine rekursive Deserialisierung zu ermöglichen, wurde Serializable.from_dict verwendet. Du kannst dies anpassen, um spezifische Klassen zu unterstützen, indem du den Typ des Dictionaries überprüfst.

Mit diesen Anpassungen ist die Basisklasse Serializable generisch genug, um in verschiedenen Klassen verwendet zu werden, ohne dass spezifische Anpassungen in der Basisklasse erforderlich sind. Die Logik zur Deserialisierung kann in den abgeleiteten Klassen spezifiziert werden, falls erforderlich.

Created on Fri Jul 26 11:22:13 2024

@author: atakan
"""
import json
import numpy as np
import yaml
import os

from typing import NamedTuple

class DataAll:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def print_attributes(self):
        for key, value in vars(self).items():
            print(f"{key}: {value}")
            
    def to_dict(self):
        return vars(self)


class DataNode:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                # Wenn der Wert ein Dictionary ist, rekursiv eine DataNode erstellen
                setattr(self, key, DataNode(**value))
            else:
                setattr(self, key, value)
    
    def to_dict(self):
        result = {}
        for key, value in vars(self).items():
            if isinstance(value, DataNode):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def __getattr__(self, name):
        # Standardverhalten, falls ein Attribut nicht existiert
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

class Serializable:
    default_path = ''
    default_filename = 'default.json'
    default_storage_filename = 'def_store.json'

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
        elif isinstance(value, dict):
            return {k: self._to_serializable(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._to_serializable(item) for item in value]
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif hasattr(value, 'to_dict'):
            return value.to_dict()
        else:
            return str(value)

    def _filter_components(self, components):
        def filter_dict(d):
            if isinstance(d, dict):
                return {k: filter_dict(v) for k, v in d.items() if k not in ('fluid', 'fluids', 'all_states')}
            return d

        return {k: filter_dict(v) for k, v in components.items()}

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if key not in ('all', 'fluid', 'fluids', 'all_states'):
                if key == 'components':
                    filtered_components = self._filter_components(value)
                    result[key] = {k: self._to_serializable(v) for k, v in filtered_components.items()}
                else:
                    result[key] = self._to_serializable(value)
        return result

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
                setattr(instance, key, np.array(value))
            elif isinstance(value, dict):
                if key == 'components':
                    setattr(instance, key, cls._deserialize_components(value))
                else:
                    setattr(instance, key, value)
            else:
                setattr(instance, key, value)
        return instance

    @classmethod
    def _deserialize_components(cls, components):
        def deserialize_dict(d):
            result = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    result[k] = deserialize_dict(v)
                elif isinstance(v, list):
                    result[k] = np.array(v) if all(isinstance(i, (int, float)) for i in v) else v
                else:
                    result[k] = v
            return result

        return {k: deserialize_dict(v) for k, v in components.items()}

    def save_to_file(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(self.default_path, self.default_storage_filename)
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


# # Beispielklasse HpVal
# class HpVal(Serializable):
#     default_path = 'default_directory'
#     default_filename = 'default_file.json'
#     default_storage_filename = 'default_file_last.json'

#     def __init__(self, variables_dict=None):
#         if variables_dict:
#             for key, value in variables_dict.items():
#                 setattr(self, key, value)
# import carbatpy as cb
# #from carbatpy.heat_pump import set_fl_state
# # Beispielklasse HeatPump
# class HeatPump(Serializable):
#     default_path = 'default_directory'
#     default_filename = 'default_file_hp.json'
#     default_storage_filename = 'default_file_hp_last.json'

#     def __init__(self, fixed_points, components=None):
#         if components:
#             self.components = components
#         else: 
#             self.components = {}
#         self.fixed_points = fixed_points
#         self.fluids_ini = fixed_points["fluids_all"]
#         self.fluids = [cb.hp_simple.set_fl_state([fll, *ii], fixed_points)[0] for fll, ii in self.fluids_ini.items()]
#         self.all_states = []
#         self.m_dots = []
#         self.warning = []
#         self.evaluation = {
#             "Q_DOT_MIN": self.fixed_points["Q_DOT_MIN"],
#             "Power": 0.0,
#             "T_OUT_STORAGE_HOT": self.fixed_points["T_OUT_STORAGE_HOT"],
#             "T_OUT_STORAGE_COLD": self.fixed_points["T_OUT_STORAGE_COLD"],
#             "exergy_loss_rate": 0
#         }

if __name__ == "__main__":
    # DataAll usage;
    warning =DataAll(value=0, message= "All o.k.")
    warning.print_attributes()
    
    
    # Testen
    fixed_points = {
        "fluids_all": {"fluid1": ["Propane", 0.675], "fluid2": ["Butane", 0.0515]},
        "Q_DOT_MIN": 1000.0,
        "T_OUT_STORAGE_HOT": 363.0,
        "T_OUT_STORAGE_COLD": 250.15
    }
    
    heat_pump = HeatPump(fixed_points)
    print("HeatPump attributes:")
    print(heat_pump.all)
    
    # Serialisieren und Speichern
    heat_pump.save_to_file('heat_pump.json')
    
    # Laden und Deserialisieren
    loaded_heat_pump = HeatPump.load_from_file('heat_pump.json')
    print("Loaded HeatPump attributes:")
    print(loaded_heat_pump.all)
    
    
    
    # Example:
    class AnotherClass(Serializable):
        default_path = '/path/to/another_class'
        default_filename = 'another_class.json'
    
        def __init__(self, attribute1, attribute2):
            self.attribute1 = attribute1
            self.attribute2 = attribute2
    
    class YetAnotherClass(Serializable):
        default_path = '/path/to/yet_another_class'
        default_filename = 'yet_another_class.json'
    
        def __init__(self, attribute3, attribute4):
            self.attribute3 = attribute3
            self.attribute4 = attribute4

if __name__ == "__main__":
    # Erstellen von Instanzen und Speichern in Dateien
    instance1 = AnotherClass(attribute1='value1', attribute2=42)
    instance2 = YetAnotherClass(attribute3=np.array([1, 2, 3]), attribute4=True)
    
    # Speichern mit Standardpfad und -dateinamen
    instance1.save_to_file()
    instance2.save_to_file()
    
    # Speichern mit benutzerdefiniertem Pfad und Dateinamen
    instance1.save_to_file('/custom/path/custom_filename.json')
    instance2.save_to_file('/custom/path/custom_filename.yaml')
    
    # Laden mit Standardpfad und -dateinamen
    loaded_instance1 = AnotherClass.load_from_file()
    loaded_instance2 = YetAnotherClass.load_from_file()
    
    # Laden mit benutzerdefiniertem Pfad und Dateinamen
    loaded_instance1 = AnotherClass.load_from_file('/custom/path/custom_filename.json')
    loaded_instance2 = YetAnotherClass.load_from_file('/custom/path/custom_filename.yaml')
    
    print(loaded_instance1.to_dict())
    print(loaded_instance2.to_dict())

