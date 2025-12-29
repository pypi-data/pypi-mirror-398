# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 17:39:12 2024

@author: atakan
"""
import numpy as np
import carbatpy as cb
import scipy.optimize as opti


dir_name = cb.CB_DEFAULTS["General"]["CB_DATA"]+"\\io-cycle-data.yaml"

def _change_h_w_out(hex_act, h_out_new):
    inputs = hex_act.inputs["states"]
    out_state = {}
    in_state = {}
    for flname, value in inputs.items():
        out_state[flname] = inputs[flname]['out']
        in_state[flname] = inputs[flname]['in']
    out_state["working_fluid"][2] = h_out_new
    return in_state, out_state

def _opti_h_func( h_act_out, hex_act,  m_dot_w, verbose =False):

    run_p_cond = {"m_dot": {"working_fluid": m_dot_w}}
    instates, outstates =_change_h_w_out(hex_act, h_act_out)
    hex_act.calculate(instates, outstates,run_param=run_p_cond)
    if verbose:
        print (hex_act.output["dt_mean"],  hex_act.warning)
    if hex_act.warning.value > 2:
        return +100
    return np.abs(hex_act.output["dt_mean"])

def hex_opti_work_out(self, run_p_cond, verbose =False):
    self.calculate(run_param=run_p_cond)
    if verbose:
        print(f"opti_work_out: T-mean before optimization= {condenser.output['dt_mean']} K")
    # condenser._change_h_w_out =_change_h_w_out
    tolerance = 1e-2
    max_iter = 240
    h_act = self.output["state_out"]["working_fluid"][2] *1.005
    dh = h_act *.051
    bound_act = opti.Bounds(lb =h_act-dh, ub = h_act+dh)

    result = opti.minimize(_opti_h_func,
                       h_act,
                       args=(
                             self,
                             m_dot_w),
                       method='Nelder-Mead',
                       tol=tolerance,
                       bounds=bound_act,
                       options={"maxiter": max_iter, # can take long!
                                "disp": True})
    if verbose:
        print(f"T-mean before optimization: {result.fun} K\n{result}")
    

# ================ CALCULATIONS ==============================
# ------ Start/initial condition ----
# but the mass flow rate is yet unknown, plotting must be delayed
start = cb.comp.Start("start", dir_name, m_dot=10e-3)

# ----- compressor --------------
# prescribed power, working_fluid mass flow rate is calculated here
run_p_comp = {"power": 1500.}
compressor = cb.comp.FlowMachine("compressor", dir_name)
p_high = compressor.config['working_fluid']['p_high']
compressor.calculate(start.output["state_out"],
                     {'working_fluid': [600, p_high, 5e5]},
                     run_param=run_p_comp)  # ,  m_dot=10e-3)
# for the output only p_high is used! Now m_dot is known for the working fluid.
m_dot_w = compressor.output["m_dot"]
start = cb.comp.Start("start", dir_name, m_dot=m_dot_w)

# ----- coondenser --------------
run_p_cond = {"m_dot": {"working_fluid": m_dot_w}}

condenser = cb.comp.StaticHeatExchanger("condenser", dir_name)

condenser.calculate(run_param=run_p_cond)
print(f"T-mean before optimization: {condenser.output['dt_mean']} K")
# condenser._change_h_w_out =_change_h_w_out
tolerance = 1e-2
max_iter =140
h_act = condenser.output["state_out"]["working_fluid"][2] *1.005
dh = h_act *.021
bound_act = opti.Bounds(lb =h_act-dh, ub = h_act+dh)

result = opti.minimize(_opti_h_func,
                   h_act,
                   args=(
                         condenser,
                         m_dot_w),
                   method='Nelder-Mead',
                   tol=tolerance,
                   bounds=bound_act,
                   options={"maxiter": max_iter, # can take long!
                            "disp": True})
print(f"T-mean before optimization: {result.fun} K\n{result}")