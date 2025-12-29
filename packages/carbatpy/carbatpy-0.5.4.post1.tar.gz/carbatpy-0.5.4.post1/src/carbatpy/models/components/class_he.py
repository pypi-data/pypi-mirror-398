# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 16:42:44 2024
heat-exchanger class

@author: welp
"""

import carbatpy as cb
import numpy as np
from scipy.optimize import fsolve
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import carbatpy.models.components.heat_transfer as heat_transfer
import time


class heat_exchanger:
    """
    class for static heat-exchanger, different configurations in future (?),
    start with double pipe counterflow heat-exchanger
    start: get outlet temperature with area A (fixed)
    
    """
    def __init__(self, fluids, inlet_states, mdot, resolution):
        self.fluids = fluids
        self.state_in_wf = inlet_states[0]
        self.state_in_sf = inlet_states[1]
        self.mdot_wf = mdot[0]
        self.mdot_sf = mdot[1]
        self.resolution = resolution
        
    def geo_A(self, A):
        self.A = A # please use Ai (inner tube surface) as reference
        self.include_pressure_loss = False
        
    def geo_double_pipe(self, di, Di, da, Da, l, lam_tube, method, incl_pr_loss=True):
        self.di = di
        self.Di = Di
        self.da = da
        self.Da = Da
        self.l = l
        self.A = np.pi * self.di * self.l
        self.method = method
        self.lam_tube= lam_tube
        self.include_pressure_loss = incl_pr_loss
        
    def calc_NTU(self, U_i=0):
        """
        calculate heat-exchanger with NTU cell-method

        Parameters
        ----------
        U_i : TYPE, optional
            DESCRIPTION. The default is 0. -> local heat-transfer coefficient
            is calculated. Then please define NTU-method. If set to value,
            constant U_i is assumed.

        Returns
        -------
        None.

        """
        
        T_guess = - (self.state_in_wf[0] - self.state_in_sf[0]) * 0.5 + \
                    self.state_in_wf[0]  # guesses start temperature for solver
        p_guess = self.state_in_sf[1]  # don't change, otherwise calculation without
                                        # pressure loss does not converge
        T_correkt, p_correct = fsolve(self._solve_compose_NTU, 
                                      [T_guess, p_guess], args=(U_i), 
                                      xtol = 0.0001)
        state1, state2 = self._compose_NTU([T_correkt, p_correct], U_i)
        self.state_out_wf = state1[-1]
        self.state_out_sf = state2[0]
        self.state_array_wf = state1
        self.state_array_sf = state2
        
    def calc_IVP(self, U_i=0):
        """
        calculates heat-exchanger with solving ODE using solve ivp

        Parameters
        ----------
        U_i : TYPE, optional
            DESCRIPTION. The default is 0. -> local heat-transfer coefficient
            is calculated. Then please define NTU-method. If set to value,
            constant U_i is assumed.

        Returns
        -------
        None.

        """
        
        T_guess = - (self.state_in_wf[0] - self.state_in_sf[0]) * 0.5 + \
                    self.state_in_wf[0]  # guesses start temperature for solver
        p_guess = self.state_in_sf[1] # don't change, otherwise calculation without
                                        # pressure loss does not converge
        T_correct, p_correct = fsolve(self._solve_ODE_ivp, [T_guess, p_guess], 
                                      args=(U_i), xtol = 0.0001)
        
        state_correct_sf = self.fluids[1].set_state([T_correct, p_correct], "TP")
        y0 = [self.state_in_wf[2],
              state_correct_sf[2],
              self.state_in_wf[1],
              state_correct_sf[1]]
        x = np.linspace(0, self.l, self.resolution)
        res = solve_ivp(lambda x, y: self._ODE_ivp(x, y, U_i), (x[0], x[-1]), y0, t_eval=x, rtol=0.1)
        
        state1 = []
        state2 = []
        
        for i in range(len(res.t)):
            state1.append(self.fluids[0].set_state([res.y[0][i], res.y[2][i]], "HP"))
            state2.append(self.fluids[1].set_state([res.y[1][i], res.y[3][i]], "HP", 
                                                   cb.fprop._TRANS_STRING))
        
        state1 = np.array(state1)
        state2 = np.array(state2)
        self.state_out_wf = state1[-1]
        self.state_out_sf = state2[0]
        self.state_array_wf = state1
        self.state_array_sf = state2
        
    def _solve_ODE_ivp(self, y_tp, U_i):
        """
        internal helper function, used to iterate solve ivp
        """
        
        T_guess, p_guess = y_tp
        x = np.linspace(0, self.l, self.resolution)
        state_guess_sf = self.fluids[1].set_state([T_guess, p_guess], "TP")
        y0 = [self.state_in_wf[2],
              state_guess_sf[2],
              self.state_in_wf[1],
              state_guess_sf[1]]
        res = solve_ivp(lambda x, y: self._ODE_ivp(x, y, U_i), (x[0], x[-1]), 
                        y0, t_eval=x, rtol=0.1)
        state2 = self.fluids[1].set_state([res.y[1][-1], res.y[3][-1]], "HP")
        
        return [self.state_in_sf[0] - state2[0],
                self.state_in_sf[1] - state2[1]]
    
        
    def _ODE_ivp(self, x, y, U_i=0):
        """ 
        internal function, ODE to call in solve_ivp
        """
        h_wf, h_sf, p_wf, p_sf = y
        
        state_wf_x = (self.fluids[0].set_state([h_wf, p_wf], "HP"))
        state_sf_x = (self.fluids[1].set_state([h_sf, p_sf], "HP", 
                                               cb.fprop._TRANS_STRING))
        
        if U_i == 0:
            R_ges, dp_wf, dp_sf= self.thermal_resistance(state_wf_x, state_sf_x)
            dp_wf = -dp_wf
        else:
            R_ges = 1/U_i
            dp_wf = 0 
            dp_sf = 0 
  
        delta_T = state_sf_x[0] - state_wf_x[0]   

        dh_wf = self.di * np.pi/R_ges * delta_T / self.mdot_wf
        dh_sf = self.di * np.pi/R_ges * delta_T / self.mdot_sf
        
        return np.array([dh_wf, dh_sf, dp_wf, dp_sf])

        
    def _get_theta(self, U_i, A_i, W_i, C_i, characteristic='counterflow'):
        """
        calculates theta = f(NTU, C) to use in NTU-method for fluid i, second 
        fluid j
    
        Parameters
        ----------
        U_i : TYPE
            DESCRIPTION. heat transfer coefficient W/(m^2K)
        A_i : TYPE
            DESCRIPTION. heat transfer area m^2
        W_i : TYPE
            DESCRIPTION. heat capacity flow W/K
        C_i : TYPE
            DESCRIPTION. W_i / W_j
        characteristic : TYPE, optional
            DESCRIPTION. The default is 'counterflow'.
    
        Returns
        -------
        theta : TYPE
            DESCRIPTION. dimensionless temperature difference (Ti_in - Ti_out) 
                                                            / (Ti_in - Tj_in)
    
        """
        NTU = U_i * A_i / W_i
        if characteristic == "counterflow":
            theta = (1 - np.exp(NTU * (C_i - 1))) \
                     / (1 - C_i * np.exp(NTU * (C_i - 1)))   
                     # VDI heat atlas (2013) C1-table 3                           
        elif characteristic == "parallelflow":
            theta = (1 - np.exp(- NTU * (C_i + 1))) \
                     / (1 + C_i) # VDI heat atlas (2013) C1-table 3
        return theta
    
    
    def _solve_compose_NTU(self, y, U_i):
        """
        helper function to solve compose_NTU
    
        Parameters
        ----------
        y : TYPE
            DESCRIPTION. [T_sf_outlet, p_sf_outlet] to guess
        Returns
        -------
        TYPE
            DESCRIPTION. difference prescribed inlet j temperature - 
            calculated inlet j temperature, and same for pressure 
    
        """    
        state1, state2 = self._compose_NTU(y, U_i)
        #print(state2[-1])
        return [self.state_in_sf[0] - state2[-1][0],
                self.state_in_sf[1] - state2[-1][1]]
    
    def _compose_NTU(self, y, U_i):
        """
        uses cell method NTU from VDI heat atlas. currently only for 
        counterflow due to energy balance. Starts with inlet states for fluids 
        i and j and alterates outlet temperature for fluid j. Entire heat 
        exchanger is subsequently calculated from left to right. Cell on the 
        left: A, cell on the right: Z. Can be called with solve_compose_NTU 
        or independantly.
    
        Parameters
        ----------
        y : TYPE
            DESCRIPTION. outlet temperature of secondary fluid in cell A [K]
                        and outlet pressure of secondary fluid in cell A [Pa]
        U_i : TYPE
            DESCRIPTION. The default is 0. -> local heat-transfer coefficient
            is calculated. Then please define NTU-method. If set to value,
            constant U_i is assumed.
    
        Returns
        -------
        state1 : TYPE
            DESCRIPTION. array of state arrays fluid i. Line 0 cell A, line 
            (-1) cell Z
        state2 : TYPE
            DESCRIPTION. array of state arrays fluid j. Line 0 cell A, line 
            (-1) cell Z
    
        """
        T2A, p2A = y
        
        A_array = np.full(self.resolution, self.A/self.resolution) 
        # each cell is calculated with same area
        
        # initialize help variables to iteratate
        T2 = np.zeros(len(A_array))
        W1 = np.zeros(len(A_array))
        W2 = np.zeros(len(A_array))
        C2 = np.zeros(len(A_array))
        state1 = np.zeros((len(A_array), len(self.state_in_wf)))
        state2 = np.zeros((len(A_array), len(self.state_in_sf)))
        
        # set start values in array
        state1[0] = self.state_in_wf
        T2[0] = T2A
        state2[0] = self.fluids[1].set_state([T2A, p2A], \
                                             "TP", cb.fprop._TRANS_STRING)
        
        # iterate over cells
        for i in range(len(A_array)-1):
            W2[i] = self.mdot_sf * state2[i][10]
            if 0 < state1[i][5] < 1: # heat capacity of working fluid infinite
                C2[i] = 0
            else: # fluid i also 1phase
                W1[i] = self.mdot_wf * self.fluids[0].set_state([state1[i][0], state1[i][1]]\
                                         , "TP", cb.fprop._TRANS_STRING)[10]
                C2[i] = W2[i] / W1[i]
            
            if U_i == 0: 
                R, dp_wf, dp_sf = self.thermal_resistance(state1[i], state2[i])
                U_local = 1/R
            else:
                U_local = U_i
            
            theta = self._get_theta(U_local, A_array[i], W2[i], C2[i])
            
            try:
                T2[i+1] = (theta * state1[i][0] - T2[i]) / (theta-1)
            except:
                print("wait")
            if self.include_pressure_loss == True:
                delta_p_wf = -dp_wf * self.l / self.resolution
                delta_p_sf = dp_sf * self.l / self.resolution
                
            else:
                delta_p_wf = 0
                delta_p_sf = 0
            
            state2[i+1] = self.fluids[1].set_state([T2[i+1], 
                                                    state2[i][1] + delta_p_sf], 
                                                   "TP", 
                                                   cb.fprop._TRANS_STRING
                                                   )
            h1B = self.mdot_sf / self.mdot_wf \
                * (state2[i+1][2] - state2[i][2]) + state1[i][2]
            try:
                state1[i+1] = self.fluids[0].set_state([h1B, state1[i][1] + delta_p_wf], 
                                                   "HP")
            except:
                print("wait")
        
        return state1, state2
    
    def thermal_resistance(self, state_wf_x, state_sf_x):
        """
        thermal resistance for double-pipe

        Parameters
        ----------
        state_wf_x : TYPE
            DESCRIPTION.
        state_sf_x : TYPE
            DESCRIPTION.

        Returns
        -------
        R_ges : TYPE
            DESCRIPTION.

        """
        fluidstate_wf_x = self.fluids[0].set_state([state_wf_x[0], 
                                                    state_wf_x[1]], "TP", 
                                                   output="FluidState")
        fluidstate_sf_x = self.fluids[1].set_state([state_sf_x[0], 
                                                    state_sf_x[1]], "TP", 
                                                   cb.fprop._TRANS_STRING, 
                                                   output="FluidState")
        
        alpha_sf, dp_sf = heat_transfer.alpha_1P(self.fluids[1], fluidstate_sf_x, self.mdot_sf, 
                                                 self.l, self.da, self.Di)
        alpha_wf, dp_wf = heat_transfer.alpha_km(self.fluids[0], fluidstate_wf_x, 
                                                 self.mdot_wf, self.method, 
                                                 self.l, self.di)
        
        # heat transfer resistance
        R_sf = self.di/(alpha_sf*self.Di) # convection secondary fluid
        R_tube = np.log(self.Di/self.di) * self.di / self.lam_tube # conduction tube
        R_wf = 1/alpha_wf # convection working fluid

        R_ges = R_sf + R_tube + R_wf
        return R_ges, dp_wf, dp_sf
    
    def diagram(self, ordinate=0, second_yaxis=False):
        """
        plots diagram, abscissa area, ordinate can be chosen in same order of 
        state array: ("Temperature", "Pressure", "spec_Enthalpy",
                        "spec_Volume", "spec_Entropy", "quality",
                        "spec_internal_Energy",
                        "viscosity", "thermal_conductivity",
                        "Prandtl_number", "k_viscosity", "molecular_mass",
                        "speed_of_sound")

        Parameters
        ----------
        ordinate : TYPE, optional
            DESCRIPTION. The default is 0.

        Returns
        -------
        None.

        """        

        fig, ax1 = plt.subplots()
        x = np.linspace(0, self.resolution-1, self.resolution) \
                     * self.A/self.resolution

        ax1.plot(x, self.state_array_wf[:, ordinate], 'r:o', 
                 label='Working Fluid', markersize=5)
        ax1.set_xlabel('A [m^2]')
        
        if second_yaxis == True:
            ax1.tick_params(axis='y', labelcolor='r')
            ax1.set_ylabel(cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'][ordinate], 
                           color='r')

            ax2 = ax1.twinx()
            # Plot the secondary fluid on the second y-axis
            ax2.plot(x, self.state_array_sf[:, ordinate], 'b--s', 
                     label='Secondary Fluid', markersize=5)
            ax2.set_ylabel(cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'][ordinate], 
                           color='b')
            ax2.tick_params(axis='y', labelcolor='b')
        else:
            ax1.set_ylabel(cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'][ordinate])
            ax1.plot(x, self.state_array_sf[:, ordinate], 'b--s', 
                     label='Secondary Fluid', markersize=5)

        
        # Add title, legend, and grid
        plt.title(cb.CB_DEFAULTS["Fluid_Defaults"]['Property_Names'][ordinate] \
                  + ' vs Area')
        fig.legend(loc="upper right", bbox_to_anchor=(1,1), 
                   bbox_transform=ax1.transAxes)
        ax1.grid(True)
        
        plt.show()
        
if __name__ == "__main__":
    
    #for simple calculation with A
    U_i = 250
    A = 0.12
    mdot_1, mdot_2 = 0.02, 0.04
    cells = 40 # resolution
    method = "Cavallini_Smith_Zecchin"
    
    #testcase 1. Attention! Refprop only works correctly, if restart console
    FLUID1 = "Propane * Pentane"
    comp1 = [.5, .5]
    fluid1= cb.fprop.init_fluid(FLUID1, comp1)
    st1_in = fluid1.set_state([380., 0.5], "TQ")
    
    FLUID2 = "water"
    comp2 = [1]
    fluid2 = cb.fprop.init_fluid(FLUID2, comp2)
    st2_in =  fluid2.set_state([300., 6e5], "TP", cb.fprop._TRANS_STRING)
    
    
    my_first_he =heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)
    my_first_he.geo_A(A)
    my_first_he.calc_NTU(U_i)
    my_first_he.diagram()
    
    #for calculation including heat transfer coefficients + geometry
    my_second_he = heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)

    my_second_he.geo_double_pipe(10e-3, 14e-3, 18e-3, 22e-3, 4, 15.4, method)
    st_2 = time.time()
    my_second_he.calc_NTU()
    et_2 = time.time()
    my_second_he.diagram()
    my_second_he.diagram(1, True)
    
    print(f"NTU-cell-method: {et_2-st_2} s")
    
    #for solve IVP
    
    my_third_he = heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)
    
    my_third_he.geo_double_pipe(10e-3, 14e-3, 18e-3, 22e-3, 4, 15.4, method)
    st_3 = time.time()
    my_third_he.calc_IVP()
    et_3 = time.time()
    my_third_he.diagram()
    my_third_he.diagram(1, True)
    
    print(f"solve_ivp-method: {et_3-st_3} s")
    
    # evaporator
    FLUID1 = "Propane * Pentane"
    comp1 = [.5, .5]
    fluid1= cb.fprop.init_fluid(FLUID1, comp1)
    st1_in = fluid1.set_state([296., 0.5], "TQ")
    
    FLUID2 = "water"
    comp2 = [1]
    fluid2 = cb.fprop.init_fluid(FLUID2, comp2)
    st2_in =  fluid2.set_state([360., 6e5], "TP", cb.fprop._TRANS_STRING)
    
    my_fourth_he = heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)
    my_fourth_he.geo_A(A)
    my_fourth_he.calc_NTU(U_i)
    my_fourth_he.diagram()
    my_fourth_he.diagram(1, True)
    
    # evaporator with NTU and alpha, dp
    method = "Chen_Bennett"
    
    my_fifth_he = heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)
    my_fifth_he.geo_double_pipe(10e-3, 14e-3, 18e-3, 22e-3, 4, 15.4, method)
    my_fifth_he.calc_NTU()
    my_fifth_he.diagram()
    my_fifth_he.diagram(1, True)
   
    # evaporator with solve ivp and alpha, dp
    
    my_sixth_he = heat_exchanger([fluid1, fluid2], [st1_in, st2_in],
                                 [mdot_1, mdot_2], cells)
    my_sixth_he.geo_double_pipe(10e-3, 14e-3, 18e-3, 22e-3, 4, 15.4, method)
    my_sixth_he.calc_IVP()
    my_sixth_he.diagram()
    my_sixth_he.diagram(1, True)
    
    # Graveyard
    # =============================================================================
    # SOLVE BVP NOT STABLE    
    #    def calc_BVP(self):
    #         x = np.linspace(0, self.l, self.resolution)
    #         y0 = [np.linspace(self.state_in_wf[2], self.state_in_wf[2], self.resolution),
    #               np.linspace(self.state_in_sf[2], self.state_in_sf[2], self.resolution),
    #               np.linspace(self.state_in_wf[1], self.state_in_wf[1], self.resolution),
    #               np.linspace(self.state_in_sf[1], self.state_in_sf[1], self.resolution)]
    # 
    #         res = solve_bvp(self._ODE_BVP, self._bc, x, y0, tol=1e-1, max_nodes=100)
    # 
    #         # Auslesen Berechnungsergebnisse
    #         h_wf_res = res.y[0]
    #         h_sf_res = res.y[1]
    #         p_wf_res = res.y[2]
    #         p_sf_res = res.y[3]
    # 
    #         # Berechnen des Temperaturverlaufes
    #         state_wf = []
    #         state_sf = []
    #         for l in range(len(h_wf_res)):
    #             state_wf.append(self.fluids[0].set_state([h_wf_res[l], p_wf_res[l]], "HP"))
    #             state_sf.append(self.fluids[1].set_state([h_sf_res, p_sf_res], "HP", cb.fprop._TRANS_STRING))
    #         self.state_array_wf = np.array(state_wf)
    #         self.state_array_sf = np.array(state_sf)
    #         
    #     def _bc(self, y_left, y_right):
    #         return np.array([y_left[0] - self.state_in_wf[2],
    #                          y_right[1] - self.state_in_sf[2],
    #                          y_left[2] - self.state_in_wf[1],
    #                          y_right[3] - self.state_in_sf[1]])
    #         
    #     def _ODE_BVP(self, x, y):
    #         h_wf = y[0]
    #         h_sf = y[1]
    #         p_wf = y[2]
    #         p_sf = y[3]
    #         state_wf_x = []
    #         state_sf_x = []
    #         R_ges = []
    #         dp_wf = []
    #         dp_sf = []
    #         
    #         for i in range(len(h_wf)):        
    #             state_wf_x.append(self.fluids[0].set_state([h_wf[i], p_wf[i]], "HP"))
    #             state_sf_x.append(self.fluids[1].set_state([h_sf[i], p_sf[i]], "HP", cb.fprop._TRANS_STRING))
    # 
    #             R_gesi, dp_wfi, dp_sfi= self.thermal_resistance(state_wf_x[i], state_sf_x[i])
    #             R_ges.append(R_gesi)
    #             dp_wf.append(-dp_wfi)
    #             dp_sf.append(dp_sfi)
    #         state_wf_x = np.array(state_wf_x)
    #         state_sf_x = np.array(state_sf_x)
    #         R_ges = np.array(R_ges)
    #         dp_wf = np.array(dp_wf)
    #         dp_sf= np.array(dp_sf)
    #         delta_T = state_sf_x[:,0] - state_wf_x[:,0]   
    # 
    #         dh_wf = self.di * np.pi/R_ges * delta_T / self.mdot_wf
    #         dh_sf = self.di * np.pi/R_ges * delta_T / self.mdot_sf
    # 
    #         dy = np.array([dh_wf, dh_sf, dp_wf, dp_sf])
    #         #print(y)
    #         return dy
    # =============================================================================
    
    
