# -*- coding: utf-8 -*-
"""
find the two points with the (nearly) minimum distance between two curves
Created on Tue Nov 14 13:19:00 2023

@author: atakan
"""

import numpy as np
import matplotlib.pyplot as plt



x = np.linspace(0, 12)
shift =1
line = -1.9*x + 5+shift
second = 5*np.sin(x) + 5 * x + 4

f,ax = plt.subplots(1,1)
ax.plot(x,line)
ax.plot(x,second)
difference =line-second
#difference[25] =1
ax.plot(x,difference,"v")
sum_shifted = np.sum(np.abs(difference))
grad = np.gradient(difference,x)
grad2 = np.gradient(grad,x)
ax.plot(x,grad,":")
ax.plot(x,grad2,"o")
idx = np.where(np.sign(grad[:-1]) != np.sign(grad[1:]))[0] + 1
idx_min =np.where(grad2[idx]>0)
x_min =x[idx[idx_min]]
print(idx, difference[idx], grad[idx],grad2[idx], x_min)
# if len(idx) > 0:
#     wanted = min(d_temps[idx] - self.d_temp_separation_min)
# else:
#     wanted = mind_temp-self.d_temp_separation_min
