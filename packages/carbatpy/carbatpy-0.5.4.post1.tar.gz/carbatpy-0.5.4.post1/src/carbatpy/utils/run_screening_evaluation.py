# -*- coding: utf-8 -*-
"""
Run script to evaluate the fluid screening, together with the compressor model

which are stored in two csv-files. First they are sorted then concatenated.
Afterwards, the Paeroto optimal values are selected, plotted and stored.


Created on Mon Feb 12 17:01:22 2024

@author: atakan
"""

from paretoset import paretoset
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sbn
import carbatpy as cb


RUN_NO = 1

f_add ="-sort-rlt-4val" # change this name to have unique file names for each run
directory = r"C:\Users\atakan\sciebo\results\optimal_hp_fluid\fluid_select_restricted\2024-02-12-16-55-ProEthPenBut"

filename1 = directory + r"\\2024-02-12-16-55-ProEthPenBut.csv"
pareto_file = filename1.split(".")[0]+'-sort-evaluated.csv'

f_name = filename1.split(".")[0]+f_add
filename2 = directory + \
    r"\\2024-02-12-16-55-ProEthPenBut-compressor-Roskosch.csv" # the compressor data

data_screen = pd.read_csv(filename1)
keys=data_screen.columns
fl_all =cb. property_eval_mixture.get_fluid(data_screen)
fl_col = fl_all[1]
data =data_screen.sort_values(axis=0, by=fl_col).reset_index(drop=True)
# .reset_index is important, without it, sorting gets lost after concat


eval_dat = pd.read_csv(filename2)
keys2 =eval_dat.columns
eval_sorted=eval_dat.sort_values(axis=0, by=fl_col).reset_index(drop=True)
all_keys=[*keys, *keys2]

combined_data = pd.concat([data, eval_sorted], axis=1, ignore_index=True)
combined_data.columns=all_keys
combined_data.to_csv(f_name+"-combi-new.csv")


what_act = {"x": 'spec_Volume_sup', "y": 'COP_is80', "hue": 'p_ratio',#',# 'COP_comp', #'T_glide_h',
             "size":  'spec_Volume_sup', 'style': 'Temperature_hplt'}

if RUN_NO ==0:
    
##############################################
   
    SUCCESS = cb.property_eval_mixture.data_plot(filename1, what_act)

############################################
    fluids_act, fluid_col_act, fluid_str_act = cb.property_eval_mixture.get_fluid(combined_data)

#########################################

    evaluated_data = cb.property_eval_mixture.eval_is_eff_roskosch(combined_data,
                                      filename1.split(".")[0]+'-sort-evaluated.csv')

###################################
if RUN_NO >=0: # Pareto-Optimal values are searched, for these objectives:
    objectives_act = [ 'T_glide_h',  'eff_sec_law_r_lowT', 'spec_Volume_sup','p_ratio']  #'eff_sec_law_r'] # 'spec. Volume_sup',
    sense_act = ["max", "max", "min", "min"]
    
    what_act["x"]=objectives_act[0]
    what_act["y"]=objectives_act[1]
    
    optimal_data = cb.optimize.pareto(pareto_file, [objectives_act,sense_act])
    opt_values = optimal_data["all_values"][ optimal_data["optimal_mask"]]
    opt_values.to_csv(f_name+"-pareto.csv")
    graph = sbn.relplot(data=opt_values.round(3),
                        y=what_act["y"],
                        hue=what_act["hue"],
                        size=what_act["size"],
                        
                        x=what_act["x"])
    graph.savefig(f_name+"-plot.jpg", dpi =300)
    with open(f_name+"-objectives-.txt", "w", encoding="utf-8") as file:
              file.write(str(list(zip(objectives_act,sense_act))))
              
    
    graph2 = sbn.relplot(data=optimal_data["all_values"],
                        y="is_eff",
                        hue="p_ve",
                        #size="eff_sec_law_r_lowT",
                        
                        x='spec_Volume_sup')
    graph2.savefig(f_name+"-plot_is_eff.jpg", dpi =300)
    # val = cb.property_eval_mixture.get_cycle_points(opt_values, 80)
    # val2 = cb.property_eval_mixture.get_cycle_points(opt_values, 104)
    # figure, axis =plt.subplots(1,1)
    # axis.plot(val[2,:]- val[2,:].min(),val[0,:],"o:k")
    # axis.plot(val2[2,:]- val2[2,:].min(),val2[0,:],"v:b")
    
