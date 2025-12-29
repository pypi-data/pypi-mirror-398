# -*- coding: utf-8 -*-
"""
Example how to write flexible to_dir, from_dir, save_to_file, load_from_file for classes.

Also for other instances and numpy arrays.

From ChatGPT

Created on Thu Jul 25 14:13:52 2024

@author: atakan
"""

import json
import yaml
import numpy as np

class AnotherClass:
    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {'value': self.value}

    @classmethod
    def from_dict(cls, data):
        return cls(data['value'])

class MyClass:
    def __init__(self, name, age, occupation, array, component):
        self.name = name
        self.age = age
        self.occupation = occupation
        self.array = array
        self.component = component  # Beliebig benannter Attribut

    def to_dict(self):
        # Alle Attribute extrahieren, keine Methoden und self.all ausschließen
        result = {}
        for key, value in self.__dict__.items():
            if key != 'all':  # Beispiel für ein zu ignorierendes Attribut
                if isinstance(value, np.ndarray):
                    result[key] = value.tolist()  # NumPy-Arrays in Listen konvertieren
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()  # Konvertieren, wenn `to_dict` vorhanden
                else:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data):
        instance = cls.__new__(cls)
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
                # Annahme: Listen sind NumPy-Arrays
                setattr(instance, key, np.array(value))
            elif isinstance(value, dict) and 'value' in value:
                # Annahme: Dictionary ist eine Instanz von AnotherClass
                setattr(instance, key, AnotherClass.from_dict(value))
            else:
                setattr(instance, key, value)
        return instance

    def save_to_file(self, file_path):
        try:
            data = self.to_dict()
            if file_path.endswith('.json'):
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'w') as file:
                    yaml.dump(data, file)
            else:
                raise ValueError("Unsupported file format. Use .json or .yaml/.yml")
        except Exception as e:
            print(f"Error saving to file: {e}")

    @classmethod
    def load_from_file(cls, file_path):
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
     
        
if __name__ =="__main__":
    # Beispielinstanzen erstellen
    array = np.array([1, 2, 3, 4])
    component = AnotherClass(10)
    obj = MyClass("Alice", 30, "Engineer", array, component)
    
    # Speichern der Instanz in eine JSON-Datei
    obj.save_to_file('instance.json')
    
    # Neue Instanz aus der Datei erstellen
    new_obj = MyClass.load_from_file('instance.json')
    if new_obj:
        print(new_obj.__dict__)
