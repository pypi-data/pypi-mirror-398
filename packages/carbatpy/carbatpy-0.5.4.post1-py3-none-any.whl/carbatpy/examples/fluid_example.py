#!/usr/bin/env python
# coding: utf-8

# ## Fluid Properties
# Using carbatpy, the default is evaluating fluid properties with REFPROP, but along initializing a fluid you can also set props="TREND". You should have installed the package you want to use, they are not part of carbatpy!

# In[9]:


import carbatpy as cb


# Select a fluid, calculate a state using the default REFPROP and print it out:

# In[10]:


FLUID = "Propane * Pentane"
    
comp = [.5, .5]
myFluid = cb.init_fluid(FLUID, comp)

quality = 0.5       # is interpreted by carbatpy as mol/mol to calculate state
# but given back in string as kg/kg
st0 = myFluid.set_state([300., quality], "TQ")
myFluid.print_state()


# ## Properties and Units
# The properties can be accessed from a dictionary. **Units are SI** (mass base: K, kg. Pa, m), only composition is always in **mole fractions**.

# In[11]:


myFluid.val_dict


# or using the properties (FluidState Class):

# In[12]:


myFluid.properties.enthalpy


# You are interested in transport properties? First check the Default settings:

# In[13]:


cb.CB_DEFAULTS


# Then we need the TRANS_STRING the default is the THERMOSTRING:

# In[14]:


TS = cb.CB_DEFAULTS['Fluid_Defaults']['TRANS_STRING']
state = myFluid.set_state([300, 1e5], "TP", TS)


# In[15]:


myFluid.val_dict


# In[ ]:





# In[ ]:





# In[ ]:





# ## Return Value
# By default the returned output (state) is a list (in the same order, as above, but without x,y, z), which may be more convenient to use, but the order of the properties after the internal energy may change in later versions.
# by setting the keyword "output" = "FluidState", you can get an instanse of FluidState as return value and you can access the properties by name (here: spec. enthalpy):
# 
# 

# In[19]:


my_prop = myFluid.set_state([300, 1e5], "TP",output="FluidState")
print("FluidState:\n",my_prop.state_to_dict(),f"\nEnthalpy: {my_prop.enthalpy}\n")
print(f"\nstate:\n {state}")


# ## TREND
# If you installed it, you can use it. It needs some additional input (see TREND manual). Although we initialize with "TP" (temperature, pressure), you can use it with other combinations also, if they are installed in TREND. The units are as said above.
# Transport property evaluation will be implemented soon, but the calculated values differ from those in REFPROP and currently mixtur transport properties cannot be evaluated.
# Both cannot handle two-phase fluidtransport properties!

# In[ ]:


TREND = cb.CB_DEFAULTS['Fluid_Defaults']['TREND']

if TREND["TREND_INSTALLED"]:
    trend_dll = TREND["TREND_DLL"]
    trend_path = TREND["TREND_PATH"]
    
tr_dict = {"Input": "TP",
               'calctype': "H",
               'fluids': FLUID,
               "moles": comp,
               "eos_ind": [1, 1],
               'mix_ind': 1,
               'path': trend_path,
               'unit': 'specific',
               'dll_path': trend_dll}
my_trend_fluid = cb.init_fluid(FLUID, comp, props="TREND", args= tr_dict)


# In[ ]:


state = my_trend_fluid.set_state([300, 1e5], "TP")
my_trend_fluid.val_dict


# In[ ]:




