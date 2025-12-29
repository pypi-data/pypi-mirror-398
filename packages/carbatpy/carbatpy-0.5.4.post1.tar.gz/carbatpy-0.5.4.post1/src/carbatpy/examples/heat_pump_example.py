#!/usr/bin/env python
# coding: utf-8

# # Heat Pump Example
# 
# 
# How to calculate a heat pump with carbatpy.
# There are two storages (cold and hot) running between prescribed temperatures with defined fluids.

# In[17]:


import carbatpy as cb


# ## Select the input file (yaml or json works):

# In[18]:


DEFAULT_DIR =  cb.CB_DEFAULTS["General"]["CB_DIR"]+"\\data\\"
DEFAULT_FILE = DEFAULT_DIR+"hp-input-dictvariables"


# The content of the (here: json) file is shown below.
# It includes the wanted minimum separation between fluid temperatures D_T_MIN, superheating before compressor, isentropic efficiency (=const. at the moment), the pressures, fluids and their composition in both storages and the working fluid. If **P_Working["setting"] =="auto"** , the pressures will be determined acording to the storage temperatures, but this can fail.
# Alternatively "setting" can be anything else, then the two pressures (p_low for the evaporator, p_high for the condenser, all in *Pa*) will be used together with the temperatures (and T-differences) listed. Again, if the values are not chosen properly, this will fail, therefore check the *warning* (see below).
# 
# 
# 
# 
#     {
#         "D_T_MIN": 4.0,
#         "D_T_SUPER": 5,
#         "ETA_S_C": 0.7,
#         "P_IN_STORAGE_COLD": 500000.0,
#         "P_IN_STORAGE_HOT": 500000.0,
#         "P_WORKING": {
#             "optimize": "None",
#             "setting": "auto",
#             "p_low": 0.0,
#             "p_high": 0.0
#         },
#         "Q_DOT_MIN": 1000.0,
#         "T_IN_STORAGE_COLD": 288.15,
#         "T_IN_STORAGE_HOT": 288.15,
#         "T_OUT_STORAGE_COLD": 250.15,
#         "T_OUT_STORAGE_HOT": 363.0,
#         "fluids_all": {
#             "WORKING": [
#                 "Propane * Butane * Pentane * Hexane",
#                 [
#                     0.75,
#                     0.05,
#                     0.15,
#                     0.05
#                 ]
#             ],
#             "STORAGE_HOT": [
#                 "Water",
#                 [
#                     1.0
#                 ]
#             ],
#             "STORAGE_COLD": [
#                 "Methanol",
#                 [
#                     1.0
#                 ]
#             ]
#         }
#     }
# 
# ## Read the inputs from the file and create an input dictionary:

# In[19]:


inputs = cb.hp_simple.HpVal.load_from_file(DEFAULT_FILE+".json")
# print(DEFAULT_FILE)

INPUTS = inputs.to_dict()


# ## Create a new instance of HeatPump with the wanted data:

# In[20]:


hpn = cb.hp_simple.HeatPump( INPUTS)
print(hpn.evaluation)


# **Calculate the cop** and further values of the heat pump and plot it:

# In[21]:


cop_n = hpn.calc_heat_pump(verbose=True)
hpn.hp_plot()
print(f"COP: {cop_n:.3f}")


# ## Get the results
# Further **Evaluation results** are found here:

# In[22]:


hpn.evaluation


# Mass flow rates are calculated for a fixed value of the heat flow rate at high temperature $\dot Q_h$.
# The mean temperature differences are calculted for each heat exchanger using the (typically) 50 points along the heat exchanger. It can be used to estimate heat exchanger sizes:
# $\dot Q = UA \Delta T_{mean}$
# 
# ## Check for warnings
# If the temperature curves cross with the given T-p-values, you will get warnings and you should not use the results. *warning* is a list with the problem of each device listed, if there are some:

# In[23]:


if hpn.warning:
    print(f"Problems: {hpn.warning}")


# Information about **all the calculated states** (typically 50 points per heat exchanger)
# and the modelled **components**/devices can also be obtained: 
# (They are not printed here, because the output is quite long.)

# In[24]:


all_plotted_states = hpn.all_states
component_info = hpn.components


# ## Storing
# Finally you can store all these things (in part this is done automatically, check your Results folder (if it is not set as environment variable, they are in your TEMP folder):

# In[25]:


hpn.save_to_file(cb.CB_DEFAULTS["General"]["RES_DIR"]+"\\my_results.json")
RESULTS_DIR = cb.CB_DEFAULTS["General"]["RES_DIR"]

check_res_folder = False  # set this to True, if you want check yours

if check_res_folder:
    import os
    try: # results directory set, Environment variable?
        print (os.environ['CARBATPY_RES_DIR'])
    except:
        pass
    print("RESULTS folder :", cb.CB_DEFAULTS["General"]["RES_DIR"])


# The automatically stored results can be read to a dictionary:

# In[26]:


my_dict = cb.hp_simple.read_hp_results(RESULTS_DIR +
                              "\\last_T_H_dot_plot_hp_evaluation_dict.npy")


# In[ ]:




