# -*- coding: utf-8 -*-
"""

Read and load an instance of a class from/to a file

from chatgpt 

Created on Thu Jul 25 13:40:23 2024

@author: atakan
"""

import json
import yaml

def save_instance_to_file(instance, file_path):
    # Wandle die Instanz in ein Dictionary um
    data = instance.__dict__.copy()

    if file_path.endswith('.json'):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'w') as file:
            yaml.dump(data, file)
    else:
        raise ValueError("Unsupported file format. Use .json or .yaml/.yml")

def load_instance_from_file(instance, file_path):
    if file_path.endswith('.json'):
        with open(file_path, 'r') as file:
            data = json.load(file)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r') as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)
    else:
        raise ValueError("Unsupported file format. Use .json or .yaml/.yml")

    for key, value in data.items():
        setattr(instance, key, value)
        
        
        
        
if __name__ =="__main__":
        
    # Beispielklasse
    class MyClass:
        def __init__(self, name, age, occupation):
            self.name = name
            self.age = age
            self.occupation = occupation
            self.additional_info = {"hobbies": ["reading", "hiking"], "city": "Berlin"}
    
    # Beispielinstanz erstellen
    obj = MyClass("Alice", 30, "Engineer")
    
    # Speichern der Instanz in eine JSON-Datei
    save_instance_to_file(obj, 'instance.yaml')
    
    # Neue Instanz erstellen und Werte aus der Datei laden
    new_obj = MyClass("", 0, "")
    load_instance_from_file(new_obj, 'instance.yaml')
    print(new_obj.__dict__)
