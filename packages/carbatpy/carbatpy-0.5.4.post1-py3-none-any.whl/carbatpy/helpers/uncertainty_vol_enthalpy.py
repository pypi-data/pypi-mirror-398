# -*- coding: utf-8 -*-
"""
How does the uncertainty in spec. volume influence the uncertainty in enthalpy?

A Monte Carlo approach

Created on Wed Nov 15 10:37:45 2023

@author: atakan
"""
import numpy as np
import numpy.polynomial.polynomial as pol

#import numpy.random.Generator as nrg
import matplotlib.pyplot as plt

import carbatpy as cb

_RESULTS_ = cb._RESULTS_DIR


# FLUID = "Propane * Ethane * Pentane *Butane"
# #comp = [.75, 0.05, 0.15, 0.05]
# x1 = 0.
# x2 = 0.3
# x3 = 0.2
# x4 = 1 - x1-x2-x3
# comp = [x1, x2, x3, x4]  # [0.164,.3330,.50300,0.0]

###############
FLUID = "Butane * CO2"
comp = [0.8, 0.2]
print(f"{FLUID}, composition:\n{comp}")


flm = cb.fprop.FluidModel(FLUID)
myFluid = cb.fprop.Fluid(flm, comp)
temp_low = 300.
delta_temp = 10
n_points = 21
pressure_ratios = np.linspace(1, 11, n_points)
state_in = myFluid.set_state([temp_low, 1.], "TQ")
p_low = state_in[1]
state_in = myFluid.set_state([temp_low + delta_temp, p_low], "TP")
results = []
entropy = state_in[4]
for p_out in pressure_ratios:
    results.append(myFluid.set_state([p_out*p_low, entropy], "PS"))

results = np.array(results)
h_initial = np.trapz(results[:,3], results[:,1])
f, ax = plt.subplots(2, 2)
# fit a 'polytropic' [degree: 2] to the Refprop data log(v) vs log(p)
para = pol.polyfit(np.log10(results[:, 1]), np.log10(results[:, 3]), 2)
const = results[0, 1]* results[0, 3]**(-para[1])
ax[0,0].plot(results[:, 1], results[:, 3], "x")
#ax[0].plot(results[:, 1], (const  /results[:, 1])**(-1/para[1]))


# ax[0].plot(np.log10(results[:, 1]), np.log10(results[:, 3]), "x")
ax[0,0].plot(results[:, 1], 10**pol.polyval(np.log10(results[:, 1]), para))

para_neu =para

ax[0,0].plot(results[:, 1], 10**pol.polyval(np.log10(results[:, 1]), para))

# Now some scatter, two methods a) scatter on each v-point [middle plot] and
# b) scatter on 3 points (see indx) and fit a polytropic through these points [right plot]
# and evaluate the intergral for each appoach
np.random.normal()
dh = [] # approach a)-Results
dh_alternative = []  # approach b) results
dh_shift =[]  # the whole curve is shifted multiplied by y single :.3gfactor
indx = [0, n_points//2, -1]
order = 2
if len(indx) < 3:
    order = 1
for sample in range(1000):
    factors = np.random.normal(1, 0.08, n_points)
    f2 = factors[indx]
    pres_2 = pressure_ratios[indx]*p_low
    para2 = pol.polyfit(np.log10(pres_2), np.log10(results[indx, 3]*f2), order)
    p = pressure_ratios*p_low
    # volumes = 10**pol.polyval(np.log10(p), para)*factors
    volumes = results[:,3]*factors
    volumes2 = 10**pol.polyval(np.log10(p), para2)# *factors
    # volumes3 = factors[0]* 10**pol.polyval(np.log10(p), para)
    volumes3 = results[:,3]*factors[0]
    ax[0,1].plot(p, volumes)
    ax[1,1].plot(p, volumes2)
    ax[1,0].plot(p, volumes3)
    dh.append(np.trapz(volumes, p))
    dh_alternative.append(np.trapz(volumes2, p))
    dh_shift.append(np.trapz(volumes3, p))
dh = np.array(dh)
dh_alternative = np.array(dh_alternative)
dh_shift = np.array(dh_shift)

f.savefig(_RESULTS_+"v_uncertain.png")
print (f"Initial delta h: {h_initial:.2f}")
print(f"independent scatter on every point, mean {dh.mean():.2f}, std-dev {dh.std():.2f}, relative {dh.std()/dh.mean():.2f}")
print(f"scatter on 3 points &  fit, mean {dh_alternative.mean():.2f}, std-dev { dh_alternative.std():.2f}, relative {dh_alternative.std()/dh_alternative.mean():.2f}")
print(f" same scatter on all points &  fit, mean {dh_shift.mean():.2f}, std-dev {  dh_shift.std():.2f}, relative {dh_shift.std()/dh_shift.mean():.2f}")
