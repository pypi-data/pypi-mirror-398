# -*- coding: utf-8 -*-
"""
find the straight line which just touches a curve, while having the minimum
area between the curves.

2024-02-11
part of carbatpy

@author: atakan
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize


def straight_diff(param, values, below=True):
    """
    Calculating the integral between a straight line and points from a curve

    the line is defined by the param values [slope,intercept], values[0,:] are
    the x values, values[1,:] are the y-values. below decides, whether the
    straight line should be below or not. This function is used for
    minimization.
    If the curves cross each other or if the line is on the wrong side,
    a large value is returned.

    Parameters
    ----------
    param : list of float
        [slope,intercept].
    values : numpy.array [2,n_points]
        values[0,:] are the x values, values[1,:] are the y-values.
    below : boolean, optional
        is the straight line below. The default is True.

    Returns
    -------
    float
        integral of the difference between the curves.

    """
    difference = values[1, :] - (param[0] * values[0, :] + param[1])

    positive = np.any(difference > 0)
    negative = np.any(difference < 0)

    crossing = (positive > 0 and negative > 0)
    wrong_side = (positive > 0 and not below) or (negative > 0 and below)

    penalize = np.abs(100 * (values[1, :].max() - values[1, :].min())
                      * (values[0, -1] - values[0, 0]))
    if crossing or wrong_side:
        return penalize
    if below and positive > 0:
        integral = np.trapezoid(difference, values[0])

    else:
        integral = np.trapezoid(-difference, values[0])
    return integral


def find_min_approach(values_in, below=True, delta=0):
    """
    Finds a straight line which approaches a curve, without crossing.

    Mainly for finding the minimum approach of a fluid with phase change
    to a fluid with a constant heat capacity along heat transfer. One can
    select, whether the straight line should be *below* the curve or above.

    Parameters
    ----------
    values : numpy array [2,n]
        [0,n] are the x-values, [1,n] are the y-values.
    below : boolean, optional
        should the straight line be below? The default is True.
    delta : float, optional
        wanted least distance between curves (absolute value.)

    Returns
    -------
    output : dictionary
        keys are "success", "integral": the integral between curve and line,
        "line_par": slope and intercept of the line (np.array),"below":as above,
        "message": result.message from minimize}.

    """
    values = np.copy(values_in)
    factor = 1
    if below == True:
        factor = -1
    values[1] = values[1] + factor * delta
    para0 = np.polyfit(values[0], values[1], 1)
    min_val = values[1].min()
    max_val = values[1].max()
    diff_val = max_val - min_val
    if below:
        para0[1] -= diff_val
    else:
        para0[1] += diff_val
    result = minimize(straight_diff, para0, args=(values, below),
                      method='Nelder-Mead', tol=1e-4,
                      options={'maxiter': 1e3})
    difference = (values[1] - np.polyval(result.x, values[0])).mean()

    output = {"success": result.success,
              "integral": result.fun,
              "line_par": result.x,
              "below": below,
              "message": result.message,
              "mean_difference": difference - factor * delta}
    return output


def diff_mean(high, low, dist_min=0., optimize=False):
    """
    calculate the mean distance between two equally-spaced arrays

    In thermodynamics/heat exchangers for minimum approach temperature. The size
    of both arrays must be the same. If the curves cross, success will be False!

    Parameters
    ----------
    high : numpy array (length m)
       the high values.
    low : numpy array(length m)
       the low values.
    dist_min : float, optional
        minimum required distnce, must be positive. The default is 0..
    optimize : boolean, optional
        if used for optimization. The default is False.

    Returns
    -------
    dictionary or float
        for optimization the mean difference is returned, else a dictionary
        with success, mean-difference, all differences, dist_min.

    """
    success = True
    if len(high) != len(low):
        print("wrong array lengths")
        return 1e9
    difference = high - low
    mean_diff = difference.mean()
    problem = np.any(difference < dist_min)
    if problem > 0:
        success = False
    if optimize:
        if success:
            return mean_diff
        else:
            return (high.max() - low.min()) * 5
    else:
        return {"success": success,
                "mean_difference": mean_diff,
                "dist_min": dist_min,
                "all_differences": difference}


if __name__ == "__main__":
    # generating test points
    x_val = np.linspace(1, 12)
    y_val = -5 * np.sin(x_val) + 5 * x_val + 4 - 100 / x_val
    values_act = np.array([x_val, y_val]) # input for find_min_approach
    lower = np.polyval([10, -120], values_act[0])

    delta = 5
    ###############################
    # for arbitrary arays, comparison
    mean_difference = diff_mean(values_act[1], lower, 14)
    print(mean_difference)
    
    ###############################
    # finding an optimal straigh line
    solution_below = find_min_approach(values_act, True, delta)
    solution_above = find_min_approach(values_act, False, delta)

    # Plotting ####################
    figure, axis = plt.subplots(1, 1)
    axis.plot(values_act[0], values_act[1], "ko")
    axis.plot(values_act[0], lower,"g:")
    axis.plot(values_act[0], np.polyval(
        solution_below["line_par"], values_act[0]), "b")
    axis.plot(values_act[0], np.polyval(
        solution_above["line_par"], values_act[0]), "r")
