# -*- coding: utf-8 -*-
"""
Comparison of cost estimation taken from two books for reciprocating
compressors

cost2: chapter 21 of  Chemical engineering design : principles, practice and 
economics of plant and process design
Gavin Towler, Ray Sinnott. 3rd ed.; 2022

cost_function: Chemical Process Equipment Selection and Design
Third Edition
James R. Couper
W. Roy Penney
James R. Fair
Stanley M. Walas

"""


def cost_function(size, what):
    all_data = {"Compressor-Reciprocating": [2.6e5, 2700, 0.75, 93, 16800]}
    constant, multi, exponent, min_size, max_size = all_data[what]
    warning = 1
    if size > min_size and size < max_size:
        warning = 0
    cost = constant + multi * size**exponent
    return round(cost,0), warning


if __name__ == "__main__":
    size_act = 100  # kW
    what_act = "Compressor-Reciprocating"
    print(
        f"Prize of {what_act} at size {size_act}: {cost_function(size_act, what_act)}")
    horse_power = 0.735  # kW
    cost2 = round(7.19 * (size_act / horse_power)**.61 *1000, 0)
    print(f"second prize: {cost2}")
