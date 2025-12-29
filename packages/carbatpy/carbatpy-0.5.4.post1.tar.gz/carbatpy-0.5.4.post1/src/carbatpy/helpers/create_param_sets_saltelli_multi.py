# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 13:00:55 2024
use Saltelli-sequence to create parameter sample set within defined bounds,
then calls modell including multiprocessing
@author: welp
"""

import carbatpy as cb
from SALib.sample import saltelli
import time
import multiprocessing
import concurrent.futures
import numpy as np
from datetime import datetime
import os
import json

def create_saltelli_sample(dic, n):
    '''
    uses SALib to create saltelli sample

    Parameters
    ----------
    dic : TYPE
        DESCRIPTION. example: 
                    {'num_vars': 5, 
                      'names': ['dT', 'p_ve', 'p_e', 'xa', 'xb'],
                      'bounds': [[2, 25], [2, 8], [200, 600], [0.5, 0.7], [0.05, 0.29]]
                      }   
    n : TYPE
        DESCRIPTION. 2 ** n in Saltelli sequence

    Returns
    -------
    param_values : TYPE
        DESCRIPTION. parameter set

    '''
    N_sample = 2 ** n
    param_values = saltelli.sample(problem=dic, N=N_sample, calc_second_order=False)
    return param_values


def model(args):
    '''
    mock model, use wished model here
    '''
    return np.concatenate((args, [np.sum(args)]))


def process_task(modl, param_values_chunk, path):
    '''
    internal function called within multiprocessing
    '''
    results = []
    for i in range(len(param_values_chunk)):
        param_values = param_values_chunk[i, :]
        res_temp = modl(param_values)
        results.append(res_temp) 
    
    with open(path + '\\Results.txt', 'a') as file:
        for row in range(len(results)):
            file.write(','.join(map(str, results[row])) + '\n')  
    
    
def call_multiprocessing(function, param_set, path='default'):
    '''
    uses multiprocessing to call function with param_set

    Parameters
    ----------
    function : TYPE
        DESCRIPTION. function to be called in multiprocessing
    param_set : TYPE
        DESCRIPTION. parameter set, each row is one parameter set
    path : TYPE, optional
        DESCRIPTION. The default is RES_DIR

    Returns
    -------
    None.

    '''
    s = time.time()
    if path == 'default':
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        path = cb.CB_DEFAULTS["General"]["RES_DIR"] + '\\parameter_sets\\' + timestamp
    os.makedirs(path)
    num_processes = int(multiprocessing.cpu_count() / 2) 
    chunk_size = int(len(param_set) // num_processes)
    
    param_chunks = [param_set[i:i + chunk_size] for i in range(0, len(param_set), chunk_size)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = [executor.submit(process_task, function, chunk, path) for chunk in param_chunks]

    e = time.time()
    with open(path + '\\Time.txt', 'a') as f:
        f.write("\nRuntime = {} s ({} h)".format(np.round(e - s, 1), np.round((e - s) / 3600, 2)))

    with open(path + '\\parameters.txt', 'a') as f:
        f.write('input data:\n')
        f.write(json.dumps(input_data, indent=4))  # Use json.dumps for pretty printing
        f.write('\n')
        
        # Write called function
        f.write('called function:\n')
        f.write(str(function.__name__))  # Get the function name
        f.write('\n')
        
    
    
if __name__ == "__main__":
    input_data = {'num_vars': 5, 
                  'names': ['dT', 'p_ve', 'p_e', 'xa', 'xb'],
                  'bounds': [[2, 25], [2, 8], [200, 600], [0.5, 0.7], [0.05, 0.29]]
                  }   
    n = 7
    param_values = create_saltelli_sample(input_data, n)
    call_multiprocessing(model, param_values)
   