# -*- coding: utf-8 -*-
"""
Scripts for the evaluation of the results of the fluid search, e.g. finding

pareto optimal compositions.

Created on Sun Feb  4 17:38:19 2024

@author: atakan
part of carbatpy
"""
import os
import pandas

from paretoset import paretoset
import seaborn as sbn


def pareto(filename, objectives):
    """
    Compute the Pareto (non-dominated) set from the data stored in filename



    Parameters
    ----------
    filename : string
        directory/file of the csv-file to analyze. The column names will be
        used to find the objectives.
    objectives : list of strings, length [2, number_of_objectives]
        the first list in the list are the column names to search for optima.
        the second list indicates for each optimization, whether a "max" or
        "min" is searched. Here "diff" can be in a column to indicate a column
        with categories, which are analyzed separately.

    Returns
    -------
     results: dictionary
         with the whole pandas dataFrame (key:"all_values") and a list of
         booleans if True, this line of the set is pareto optimal
         (key:"optimal_mask"). Also, the "objectives" are returned.

    """
    results = {}
    try:
        results["all_values"] = pandas.read_csv(filename)
    except Exception as excep:
        text = f"{filename} vs. {os.getcwd()}, {excep}"
        raise ValueError(text) from excep

    c_names = results["all_values"].columns
    if set(objectives[0]).issubset(set(c_names)):

        results["optimal_mask"] = paretoset(
            results["all_values"][objectives[0]], sense=objectives[1])
        results["objectives"] = objectives
        return results

    print("keys do not fit, they should be one of:", c_names)
    return []


if __name__ == "__main__":
    FILENAME_ACT = r"C:\Users\atakan\sciebo\Python\carbatpy\tests\test_files\test_data_ProEthPenBut"
    FILENAME_ACT += r"\\2024-02-06-16-51-ProEthPenBut"
    objectives_act = ['p_ratio', 'T_glide_h', 'spec_Volume_sup', 'COP_is80'] # 'spec. Volume_sup',
    sense = ["min", "min", "min", "max"]
    obj_sense = [objectives_act, sense]
    res = pandas.read_csv(FILENAME_ACT+".csv")

    opti = pareto(FILENAME_ACT+".csv", obj_sense)
    optimal_data = opti["all_values"][opti["optimal_mask"]]
    optimal_data.to_csv(FILENAME_ACT+"-pareto.csv")
    with open(FILENAME_ACT+"-objectives.txt", "w", encoding="utf-8") as file:
              file.write(str(list(zip(objectives_act,sense))))

    graph = sbn.relplot(data=optimal_data,
                        y=objectives_act[-1],
                        hue=objectives_act[0],
                        size=objectives_act[1],
                        x=r'spec_Volume_sup')
    graph.savefig(FILENAME_ACT+"-plot.jpg", dpi =300)
