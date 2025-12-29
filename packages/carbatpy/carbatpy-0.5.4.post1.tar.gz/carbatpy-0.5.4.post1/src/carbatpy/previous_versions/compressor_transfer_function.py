# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 09:56:22 2024

@author: Folkers

Function for the calculation of the efficiency of a radial compressor through 
two dimensional loss correlations. Necessary input alligns with the output of 
the transfer function of geometry for compressors.

Calculations of the thermodynamical properties are done using REFPROP. 
"""

"Module Import"
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import fsolve
from CompressorRadialVelocityTriangles import CompressorRadialVelocityTriangles

# Import of the REFPROP functions
import REFPROP2Py as REFPROP
Units = 21 # Mass based units

# Import of the transfer function of geometry
from CompressorGeometryAnalytical import CompressorGeometry

# Number of Iterations
Iterations = 3



"_____________________________________________________________________________"
"Section for the stand-alone use of this transfer function"
"Compression Task Definition"
# Working fluid in REFPROP nomenclature
WorkingFluid = "co2"
WorkingFluidComposition = [1]
# Volume flow at inlet conditions [m^3/s]
InletVolumeflow = 10
### Inlet Conditions ###
# Inlet temperature [K]
InletTemperature = 300
# Inlet pressure [kPa]
InletPressure = 100000
# Calculated values
InletEnthalpy = REFPROP.refprop(WorkingFluid, "TP", "H", Units, 0, 0, InletTemperature, InletPressure, WorkingFluidComposition).Output[0]
InletEntropy = REFPROP.refprop(WorkingFluid, "TP", "S", Units, 0, 0, InletTemperature, InletPressure, WorkingFluidComposition).Output[0]
InletDensity = REFPROP.refprop(WorkingFluid, "TP", "D", Units, 0, 0, InletTemperature, InletPressure, WorkingFluidComposition).Output[0]
InletSpeedOfSound = REFPROP.refprop(WorkingFluid, "TP", "W", Units, 0, 0, InletTemperature, InletPressure, WorkingFluidComposition).Output[0]

### Outlet Conditions ###
# Outlet pressure [kPa]
OutletPressure = 1000000

def RadialCompressorDesignFunction(WorkingFluid, WorkingFluidComposition, InletPressure, InletTemperature, OutletPressure, VolumeFlow):
    """
    Function for the design of radial compressors. The basic design parameters
    are chosen through the inverse method based on the Cordier diagram. 
    Afterwards the efficiency of the designed compressor is calculated 
    iteratively through one-dimensional loss correlations.
    
    If the program determines an axial machine to be more appropriate for the
    given compression task, an error occurs.
    
    INPUT: 
        - The working fluid or mixture as appicable to REFPROP
        - The working fluid composition as mass fractions
        - The inlet pressure in Pa
        - The inlet temperature in K
        - The outlet pressure in Pa
        - The inlet volume flow in m^3/s
        
    OUTPUT: A dictionary containing the following variables in SI units
        - Isentropic Efficiency
        - Total Efficiency
        - Static Efficiency
        - Inlet Tip Diameter
        - Inlet Hub Diameter
        - Rotor Outlet Diameter
        - Stator Inlet Diameter
        - Stator Outlet Diameter
        - Rotor Blade Number
        - Stator Blade Number
        - Rotor Axial Lenght
        - Inlet Velocity
        - Outlet Velocity
        - Outlet Temperature
        - Outlet Pressure
        - Outlet Enthalpy
        - Outlet Entropy
        - Outlet Density
        - Stage Number
        - Work Coefficient
        - Flow Coefficient
        - Specific Speed
        - Specific Diameter
    """
    
    
    "Functions"
    def SlipFunctionRotor(x):
        # Function for calculating the slip factor, rotor stage number and relative
        # blade angles at rotor outlet
        # x[0]: Slip Factor
        # x[1]: Relative Blade Angle 2
        # x[2]: Rotor Blade Number
        equation1 = x[0] - ( 1-(math.cos(x[1]))**0.5 / x[2]**0.7 )
        equation2 = x[1] - ( math.atan(1/(FlowCoefficient*VarOutput[2])-math.tan(Alpha2/x[0])) )
        equation3 = x[2] - ( 2*np.pi*math.cos((Beta1MeanDiameter[i]+x[1])/2)/(0.4*math.log(1/TipDiameterRatio[i])) )
        return equation1, equation2, equation3
    
    def SkinFrictionFunctionRotor(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(RotorSkinFrictionReynoldsNumber[i]*x**0.5)))
        return equation
    
    def SkinFrictionFunctionRotor4000(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(4000*x**0.5)))
        return equation
    
    def SkinFrictionFunctionStatorVaneless(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(StatorVanelessSkinFrictionReynoldsNumber[i]*x**0.5)))
        return equation
    
    def SkinFrictionFunctionStatorVaneless4000(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(4000*x**0.5)))
        return equation   
     
    def SkinFrictionFunctionStatorVaned(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(StatorVanedSkinFrictionReynoldsNumber[i]*x**0.5)))
        return equation
    
    def SkinFrictionFunctionStatorVaned4000(x):
        equation = 1/x**0.5 - (-4*math.log10(1.255/(4000*x**0.5)))
        return equation
    # Calculated values
    IsentropicOutletEnthalpy = REFPROP.refprop(WorkingFluid, "SP", "H", Units, 0, 0, InletEntropy, OutletPressure, WorkingFluidComposition).Output[0]
    
    # Isentropic specific work over the machine  
    SpecificWork = IsentropicOutletEnthalpy-InletEnthalpy
    
    # Calling the transfer function of geometry
    MachineType, StageNumber, SpecificDiameter, SpecificSpeed, EstimatedTotalToStaticEfficiency, SizeCoefficient, Speed, OuterDiameter, WorkCoefficient, FlowCoefficient, AbsoluteVelocity, RelativeVelocity, RotationalVelocity, Alpha, VarOutput, Beta, MinimumOutletDiameter, MinimumStageNumber = CompressorGeometry(SpecificWork, InletVolumeflow, InletSpeedOfSound)
    
    # Check to ensure a radial machine is being designed
    if MachineType == "Axial":
        # raise ValueError("The input parameters resulted in an axial compressor. Consider decreasing the volume flow or increasing the specific work to arrive at a radial compressor.")
        ResultDictionary = {"Isentropic Efficiency": None,
                            "Total Efficiency": None,
                            "Static Efficiency": None,
                            "Inlet Tip Diameter": None,
                            "Inlet Hub Diameter": None,
                            "Rotor Outlet Diameter": None,
                            "Stator Inlet Diameter": None,
                            "Stator Outlet Diameter": None,
                            "Rotor Blade Number": None,
                            "Stator Blade Number": None,
                            "Rotor Axial Lenght": None,
                            "Inlet Velocity": None,
                            "Outlet Velocity": None,
                            "Outlet Temperature": None,
                            "Outlet Pressure": None,
                            "Outlet Enthalpy": None,
                            "Outlet Entropy": None,
                            "Outlet Density": None,
                            "Stage Number": None,
                            "Work Coefficient": None,
                            "Flow Coefficient": None,
                            "Specific Speed": None,
                            "Specific Diameter": None}
        print("_____________________________________________________________________________")
        print("The input parameters resulted in an axial compressor. Consider decreasing the volume flow or increasing the specific work to arrive at a radial compressor. The output is given as an empty dictionary.")
        print("_____________________________________________________________________________")
        return ResultDictionary
    
    # Rough estimation of the isentropic efficiency to use as a starting point
    EstimatedIsentropicEfficiency = np.zeros(StageNumber)+SpecificWork/StageNumber / ((SpecificWork/StageNumber+AbsoluteVelocity[0]**2/2)/EstimatedTotalToStaticEfficiency)
    OverallEstimatedIsentropicEfficiency = SpecificWork/StageNumber / ((SpecificWork/StageNumber+AbsoluteVelocity[0]**2/2)/EstimatedTotalToStaticEfficiency)
    EstimatedIsentropicRotorEfficiency = np.zeros(StageNumber)+EstimatedIsentropicEfficiency**0.5  # EstimatedIsentropicEfficiency
    EstimatedIsentropicStatorEfficiency = np.zeros(StageNumber)+EstimatedIsentropicEfficiency**0.5
    # Constant stage pressure ratio
    PressureRatio = (OutletPressure/InletPressure)**(1/StageNumber)
    Pressure3 = np.zeros(StageNumber)
    Pressure3[0] = InletPressure*PressureRatio
    for i in range(1,StageNumber):
        Pressure3[i] = Pressure3[i-1]*PressureRatio
    
    Alpha1 = Alpha[0]
    Alpha2 = Alpha[1]
    Beta1 = Beta[0]
    Beta2 = Beta[1]
    RotationalVelocity1 = RotationalVelocity[0]
    RotationalVelocity2 = RotationalVelocity[1]
    AbsoluteVelocity1 = AbsoluteVelocity[0]
    AbsoluteVelocity2 = AbsoluteVelocity[1]
    RelativeVelocity1 = RelativeVelocity[0]
    RelativeVelocity2 = RelativeVelocity[1]
    AbsoluteMeridionalVelocity1 = AbsoluteVelocity1*math.cos(Alpha1)
    AbsoluteRotationalVelocity1 = AbsoluteVelocity1*math.sin(Alpha1)
    AbsoluteMeridionalVelocity2 = AbsoluteVelocity2*math.cos(Alpha2)
    AbsoluteRotationalVelocity2 = AbsoluteVelocity2*math.sin(Alpha2)
    RelativeMeridionalVelocity1 = RelativeVelocity1*math.cos(Beta1)
    RelativeRotationalVelocity1 = RelativeVelocity1*math.sin(Beta1)
    RelativeMeridionalVelocity2 = RelativeVelocity2*math.cos(Beta2)
    RelativeRotationalVelocity2 = RelativeVelocity2*math.sin(Beta2)
    
    "_____________________________________________________________________________"
    "Setting of Variables"
    # Variables for the thermodynamic properties
    Enthalpy1 = np.zeros(StageNumber)
    Entropy1 = np.zeros(StageNumber)
    Pressure1 = np.zeros(StageNumber)
    Temperature1 = np.zeros(StageNumber)
    Density1 = np.zeros(StageNumber)
    Enthalpy2 = np.zeros(StageNumber)
    Entropy2 = np.zeros(StageNumber)
    Pressure2 = np.zeros(StageNumber)
    Temperature2 = np.zeros(StageNumber)
    Density2 = np.zeros(StageNumber)
    Enthalpy3 = np.zeros(StageNumber)
    Entropy3 = np.zeros(StageNumber)
    # Pressure3 = np.zeros(StageNumber)
    Temperature3 = np.zeros(StageNumber)
    Density3 = np.zeros(StageNumber)
    TotalEnthalpy1 = np.zeros(StageNumber)
    TotalEntropy1 = np.zeros(StageNumber)
    TotalPressure1 = np.zeros(StageNumber)
    TotalTemperature1 = np.zeros(StageNumber)
    TotalDensity1 = np.zeros(StageNumber)
    TotalEnthalpy2 = np.zeros(StageNumber)
    TotalEntropy2 = np.zeros(StageNumber)
    TotalPressure2 = np.zeros(StageNumber)
    TotalTemperature2 = np.zeros(StageNumber)
    TotalDensity2 = np.zeros(StageNumber)
    TotalEnthalpy3 = np.zeros(StageNumber)
    TotalEntropy3 = np.zeros(StageNumber)
    TotalPressure3 = np.zeros(StageNumber)
    TotalTemperature3 = np.zeros(StageNumber)
    TotalDensity3 = np.zeros(StageNumber)
    TotalRelativeEnthalpy1 = np.zeros(StageNumber)
    TotalRelativeRelativeEntropy1 = np.zeros(StageNumber)
    TotalRelativePressure1 = np.zeros(StageNumber)
    TotalRelativeTemperature1 = np.zeros(StageNumber)
    TotalRelativeDensity1 = np.zeros(StageNumber)
    TotalRelativeEnthalpy2 = np.zeros(StageNumber)
    TotalRelativeEntropy2 = np.zeros(StageNumber)
    TotalRelativePressure2 = np.zeros(StageNumber)
    TotalRelativeTemperature2 = np.zeros(StageNumber)
    TotalRelativeDensity2 = np.zeros(StageNumber)
    TotalRelativeEnthalpy3 = np.zeros(StageNumber)
    TotalRelativeEntropy3 = np.zeros(StageNumber)
    TotalRelativePressure3 = np.zeros(StageNumber)
    TotalRelativeTemperature3 = np.zeros(StageNumber)
    TotalRelativeDensity3 = np.zeros(StageNumber)
    IsentropicEnthalpy2 = np.zeros(StageNumber)
    IsentropicEnthalpy3 = np.zeros(StageNumber)
    Rothalpy1 = np.zeros(StageNumber)
    Rothalpy2 = np.zeros(StageNumber)
    SpeedOfSound1 = np.zeros(StageNumber)
    SpeedOfSound2 = np.zeros(StageNumber)
    SpeedOfSound3 = np.zeros(StageNumber)
    Viscosity1 = np.zeros(StageNumber)
    Viscosity2 = np.zeros(StageNumber)
    Viscosity3 = np.zeros(StageNumber)
    AbsoluteVelocity3 = np.zeros(StageNumber)
    LossTemperature2 = np.zeros(StageNumber)
    LossTemperature3 = np.zeros(StageNumber)
    LossPressure2 = np.zeros(StageNumber)
    LossPressure3 = np.zeros(StageNumber)
    LossTotalEnthalpy3Alt = np.zeros(StageNumber)
    
    # Variables for the Geometric Parameters
    TipDiameter1 = np.zeros(StageNumber)
    TipDiameterRatio = np.zeros(StageNumber)
    HubDiameter1 = np.zeros(StageNumber)
    Diameter2 = np.zeros(StageNumber)
    Volumeflow1 = np.zeros(StageNumber)
    Volumeflow2 = np.zeros(StageNumber)
    Volumeflow3 = np.zeros(StageNumber)
    FlowArea1 = np.zeros(StageNumber)
    FlowArea2 = np.zeros(StageNumber)
    FlowArea3 = np.zeros(StageNumber)
    BladeHeight2 = np.zeros(StageNumber)
    HubDiameter1 = np.zeros(StageNumber)
    BladeHeight1 = np.zeros(StageNumber)
    HubDiameterRatio = np.zeros(StageNumber)
    MeanDiameter1 = np.zeros(StageNumber)
    Alpha1MeanDiameter = np.zeros(StageNumber)
    Beta1MeanDiameter = np.zeros(StageNumber)
    MeanRelativeVelocity1 = np.zeros(StageNumber)
    SlipFactor = np.zeros(StageNumber)
    RotorBladeNumber = np.zeros(StageNumber)
    Beta2Blade = np.zeros(StageNumber)
    BetaMean = np.zeros(StageNumber)
    RotorBladeThickness = np.zeros(StageNumber)
    AxialClearence = np.zeros(StageNumber)
    RadialClearence = np.zeros(StageNumber)
    BackfaceClearence = np.zeros(StageNumber)
    RotorInletBladePitch = np.zeros(StageNumber)
    RotorOutletBladePitch = np.zeros(StageNumber)
    RotorInletBladeDistance = np.zeros(StageNumber)
    RotorOutletBladeDistance = np.zeros(StageNumber)
    RotorInletCrossSection = np.zeros(StageNumber)
    RotorOutletCrossSection = np.zeros(StageNumber)
    RotorInletWettedPerimeter = np.zeros(StageNumber)
    RotorOutletWettedPerimeter = np.zeros(StageNumber)
    RotorInletHydraulicDiameter = np.zeros(StageNumber)
    RotorOutletHydraulicDiameter = np.zeros(StageNumber)
    RotorHydraulicDiameter = np.zeros(StageNumber) 
    RotorAxialLength = np.zeros(StageNumber)
    RotorMeridionalLength = np.zeros(StageNumber)
    RotorHydraulicLength = np.zeros(StageNumber)
    StatorAlpha2 = np.zeros(StageNumber)
    StatorInletMachNumber = np.zeros(StageNumber)
    StatorDiameter2 = np.zeros(StageNumber)
    RotorOutletAbsoluteRotationalVelocity = np.zeros(StageNumber)
    StatorInletAbsoluteRotationalVelocity = np.zeros(StageNumber)
    StatorInletAbsoluteMeridionalVelocity = np.zeros(StageNumber)
    StatorInletAbsoluteVelocity = np.zeros(StageNumber)
    StatorInletBladeHeight = np.zeros(StageNumber)
    StatorVanelessHydraulicLength = np.zeros(StageNumber)
    StatorVanelessHydraulicDiameter = np.zeros(StageNumber)
    StatorOutletDiameter = np.zeros(StageNumber)
    StatorOutletBladeHeight = np.zeros(StageNumber)
    StatorOutletAbsoluteMeridionalVelocity = np.zeros(StageNumber)
    StatorOutletAbsoluteVelocity = np.zeros(StageNumber)
    StatorBladeNumber = np.zeros(StageNumber)
    StatorVanedMeridionalLength = np.zeros(StageNumber)
    StatorVanedHydraulicLength = np.zeros(StageNumber)
    StatorInletBladePitch = np.zeros(StageNumber)
    StatorOutletBladePitch = np.zeros(StageNumber)
    StatorSolidity = np.zeros(StageNumber)
    StatorInletBladeDistance = np.zeros(StageNumber)
    StatorOutletBladeDistance = np.zeros(StageNumber)
    StatorInletCrossSection = np.zeros(StageNumber)
    StatorOutletCrossSection = np.zeros(StageNumber)
    StatorInletWettedPerimeter = np.zeros(StageNumber)
    StatorOutletWettedPerimeter = np.zeros(StageNumber)
    StatorVanedInletHydraulicDiameter = np.zeros(StageNumber)
    StatorVanedOutletHydraulicDiameter = np.zeros(StageNumber)
    StatorVanedHydraulicDiameter = np.zeros(StageNumber)
    RotorInletReynoldsNumber = np.zeros(StageNumber)
    RotorOutletReynoldsNumber = np.zeros(StageNumber)
    StatorInletReynoldsNumber = np.zeros(StageNumber)
    StatorOutletReynoldsNumber = np.zeros(StageNumber)
    RotorRoughness = np.zeros(StageNumber)
    StatorRoughness = np.zeros(StageNumber)
    StatorBladeThickness = np.zeros(StageNumber)
    
    
    # Variables for the Losses
    IncidenceLossCoefficient = np.zeros(StageNumber)
    MeanRelativeVelocity1 = np.zeros(StageNumber)
    MeanRelativeVelocity = np.zeros(StageNumber)
    RotorSkinFrictionReynoldsNumber = np.zeros(StageNumber)
    RotorSkinFrictionCoefficient = np.zeros(StageNumber)
    RotorSkinFrictionCoefficientSmooth = np.zeros(StageNumber)
    RotorSkinFrictionCoefficientRough = np.zeros(StageNumber)
    RotorSkinFrictionRoughReynoldsNumber = np.zeros(StageNumber)
    RotorSkinFrictionLossCoefficient = np.zeros(StageNumber)
    BladeLoadingLossCoefficient = np.zeros(StageNumber)
    Km = np.zeros(StageNumber)
    MeanBladeHeight = np.zeros(StageNumber)
    MeanRelativeVelocityAlt = np.zeros(StageNumber)
    HubToShroudLossCoefficient = np.zeros(StageNumber)
    EquivalentDiffusionFactor = np.zeros(StageNumber)
    SeperationVelocity = np.zeros(StageNumber)
    AbsoluteMeridionalMixingVelocity = np.zeros(StageNumber)
    AbsoluteMeridionalWakeVelocity = np.zeros(StageNumber)
    MixingLossCoefficient = np.zeros(StageNumber)
    ClearenceLossCoefficient = np.zeros(StageNumber)
    RotorLossCoefficient = np.zeros(StageNumber)
    
    AbsoluteQuadraticMeanVelocity = np.zeros(StageNumber)
    DivergenceParameter = np.zeros(StageNumber)
    ReferenceParameter = np.zeros(StageNumber)
    DiffusionEfficiency = np.zeros(StageNumber)
    StatorVanelessDiffusionLossCoefficient = np.zeros(StageNumber)
    StatorVanelessSkinFrictionReynoldsNumber = np.zeros(StageNumber)
    StatorVanelessSkinFrictionCoefficient = np.zeros(StageNumber)
    StatorVanelessSkinFrictionCoefficientSmooth = np.zeros(StageNumber)
    StatorVanelessSkinFrictionCoefficientRough = np.zeros(StageNumber)
    StatorVanelessSkinFrictionRoughReynoldsNumber = np.zeros(StageNumber)
    StatorVanelessSkinFrictionLossCoefficient = np.zeros(StageNumber)
    StatorVanelessLossCoefficient = np.zeros(StageNumber)
    
    StatorVanedIncidenceLossCoefficient = np.zeros(StageNumber)
    AbsoluteMeridionalMixingVelocity3 = np.zeros(StageNumber)
    StatorEquivalentDiffusionFactor = np.zeros(StageNumber)
    SeperationVelocity3 = np.zeros(StageNumber)
    AbsoluteMeridionalWakeVelocity3 = np.zeros(StageNumber)
    StatorVanedMixingLossCoefficient = np.zeros(StageNumber)
    StatorVanedSkinFrictionReynoldsNumber = np.zeros(StageNumber)
    StatorVanedSkinFrictionCoefficient = np.zeros(StageNumber)
    StatorVanedSkinFrictionCoefficientSmooth = np.zeros(StageNumber)
    StatorVanedSkinFrictionCoefficientRough = np.zeros(StageNumber)
    StatorVanedSkinFrictionRoughReynoldsNumber = np.zeros(StageNumber)
    A = np.zeros(StageNumber)
    StatorVanedSkinFrictionLossCoefficient = np.zeros(StageNumber)
    StatorVanedLossCoefficient = np.zeros(StageNumber)
    StatorLossCoefficient = np.zeros(StageNumber)
    
    # Variables for the Efficiencies
    IsentropicTotalRelativeEnthalpy2 = np.zeros(StageNumber)
    IsentropicTotalRelativePressure2 = np.zeros(StageNumber)
    LossTotalRelativePressure2 = np.zeros(StageNumber)
    LossEnthalpy2 = np.zeros(StageNumber)
    LossEntropy2 = np.zeros(StageNumber)
    RotorEfficiency = np.zeros(StageNumber)
    LossTotalEnthalpy2 = np.zeros(StageNumber)
    LossTotalPressure2 = np.zeros(StageNumber)
    LossPressure2 = np.zeros(StageNumber)
    LossStatorInletTotalPressure2 = np.zeros(StageNumber)
    LossTotalPressure3 = np.zeros(StageNumber)
    LossTotalEnthalpy3 = np.zeros(StageNumber)
    LossEntropy3 = np.zeros(StageNumber)
    LossPressure3 = np.zeros(StageNumber)
    LossEnthalpy3 = np.zeros(StageNumber)
    TotalEfficiency = np.zeros(StageNumber)
    StaticEfficiency = np.zeros(StageNumber)
    IsentropicEfficiency = np.zeros(StageNumber)
    StatorEfficiency = np.zeros(StageNumber)
    
    CalculatedIsentropicEfficiency = np.zeros(Iterations)
    
    "_____________________________________________________________________________"
    "Thermodynamic Inlet Properties"
    
    
    # Applying the inlet conditions
    Enthalpy1[0] = InletEnthalpy
    Entropy1[0] = InletEntropy
    Pressure1[0] = InletPressure
    Temperature1[0] = InletTemperature
    Density1[0] = InletDensity
    
    
    "Loop for redoing the calculations and updating the efficiency estimations"
    for j in range(Iterations):
        Alpha, Beta, RotationalVelocity, AbsoluteVelocity, RelativeVelocity, WorkCoefficient, FlowCoefficient, VarOutput = CompressorRadialVelocityTriangles(SpecificSpeed, Speed, OuterDiameter, SpecificWork/StageNumber/OverallEstimatedIsentropicEfficiency, InletVolumeflow, 0)
        Alpha1 = Alpha[0]
        Alpha2 = Alpha[1]
        Beta1 = Beta[0]
        Beta2 = Beta[1]
        RotationalVelocity1 = RotationalVelocity[0]
        RotationalVelocity2 = RotationalVelocity[1]
        AbsoluteVelocity1 = AbsoluteVelocity[0]
        AbsoluteVelocity2 = AbsoluteVelocity[1]
        RelativeVelocity1 = RelativeVelocity[0]
        RelativeVelocity2 = RelativeVelocity[1]
        AbsoluteMeridionalVelocity1 = AbsoluteVelocity1*math.cos(Alpha1)
        AbsoluteRotationalVelocity1 = AbsoluteVelocity1*math.sin(Alpha1)
        AbsoluteMeridionalVelocity2 = AbsoluteVelocity2*math.cos(Alpha2)
        AbsoluteRotationalVelocity2 = AbsoluteVelocity2*math.sin(Alpha2)
        RelativeMeridionalVelocity1 = RelativeVelocity1*math.cos(Beta1)
        RelativeRotationalVelocity1 = RelativeVelocity1*math.sin(Beta1)
        RelativeMeridionalVelocity2 = RelativeVelocity2*math.cos(Beta2)
        RelativeRotationalVelocity2 = RelativeVelocity2*math.sin(Beta2)
    
        for i in range(StageNumber):
            # Calculations of the thermodynamic properties stage by stage
            TotalEnthalpy1[i] = Enthalpy1[i]+AbsoluteVelocity1**2/2 
            TotalPressure1[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, TotalEnthalpy1[i], Entropy1[i], WorkingFluidComposition).Output[0]
            TotalTemperature1[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, TotalEnthalpy1[i], Entropy1[i], WorkingFluidComposition).Output[0]
            TotalDensity1[i] = REFPROP.refprop(WorkingFluid, "HS", "D", Units, 0, 0, TotalEnthalpy1[i], Entropy1[i], WorkingFluidComposition).Output[0]
            TotalRelativeEnthalpy1[i] = Enthalpy1[i]+RelativeVelocity1**2/2 
            TotalRelativePressure1[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, TotalRelativeEnthalpy1[i], Entropy1[i], WorkingFluidComposition).Output[0]
            TotalRelativeTemperature1[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, TotalRelativeEnthalpy1[i], Entropy1[i], WorkingFluidComposition).Output[0]
            
            Rothalpy1[i] = TotalRelativeEnthalpy1[i]-RotationalVelocity1**2/2 
            Rothalpy2[i] = Rothalpy1[i]
            Enthalpy2[i] = Rothalpy2[i]-RelativeVelocity2**2/2+RotationalVelocity2**2/2 
            IsentropicEnthalpy2[i] = Enthalpy1[i]+EstimatedIsentropicRotorEfficiency[i]*(Enthalpy2[i]-Enthalpy1[i])
            Pressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, IsentropicEnthalpy2[i], Entropy1[i], WorkingFluidComposition).Output[0]
            Entropy2[i] = REFPROP.refprop(WorkingFluid, "HP", "S", Units, 0, 0, Enthalpy2[i], Pressure2[i], WorkingFluidComposition).Output[0]
            Temperature2[i] = REFPROP.refprop(WorkingFluid, "HP", "T", Units, 0, 0, Enthalpy2[i], Pressure2[i], WorkingFluidComposition).Output[0]    
            Density2[i] = REFPROP.refprop(WorkingFluid, "HP", "D", Units, 0, 0, Enthalpy2[i], Pressure2[i], WorkingFluidComposition).Output[0]
            TotalEnthalpy2[i] = Enthalpy2[i]+AbsoluteVelocity2**2/2 
            TotalPressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, TotalEnthalpy2[i], Entropy2[i], WorkingFluidComposition).Output[0]
            TotalTemperature2[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, TotalEnthalpy2[i], Entropy2[i], WorkingFluidComposition).Output[0]
            TotalDensity2[i] = REFPROP.refprop(WorkingFluid, "HS", "D", Units, 0, 0, TotalEnthalpy2[i], Entropy2[i], WorkingFluidComposition).Output[0]
            TotalRelativeEnthalpy2[i] = Enthalpy2[i]+RelativeVelocity[1]**2/2 
            TotalRelativePressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, TotalRelativeEnthalpy2[i], Entropy2[i], WorkingFluidComposition).Output[0]
            TotalRelativeTemperature2[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, TotalRelativeEnthalpy2[i], Entropy2[i], WorkingFluidComposition).Output[0]
            
            IsentropicEnthalpy3[i] = REFPROP.refprop(WorkingFluid, "PS", "H", Units, 0, 0, Pressure3[i], Entropy1[i], WorkingFluidComposition).Output[0]
            # TotalEnthalpy3[i] = TotalEnthalpy2[i]
            Enthalpy3[i] = Enthalpy1[i]+(IsentropicEnthalpy3[i]-Enthalpy1[i])/EstimatedIsentropicStatorEfficiency[i]
            # Enthalpy3[i] = TotalEnthalpy3[i]-AbsoluteVelocity1**2/2
            TotalEnthalpy3[i] = Enthalpy3[i]+AbsoluteVelocity1**2/2
            Entropy3[i] = REFPROP.refprop(WorkingFluid, "HP", "S", Units, 0, 0, Enthalpy3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            Temperature3[i] = REFPROP.refprop(WorkingFluid, "HP", "T", Units, 0, 0, Enthalpy3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            Density3[i] = REFPROP.refprop(WorkingFluid, "HP", "D", Units, 0, 0, Enthalpy3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            TotalPressure3[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, TotalEnthalpy3[i], Entropy3[i], WorkingFluidComposition).Output[0]
            TotalTemperature3[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, TotalEnthalpy3[i], Entropy3[i], WorkingFluidComposition).Output[0]
            TotalDensity3[i] = REFPROP.refprop(WorkingFluid, "HS", "D", Units, 0, 0, TotalEnthalpy3[i], Entropy3[i], WorkingFluidComposition).Output[0]
            
            SpeedOfSound1[i] = REFPROP.refprop(WorkingFluid, "TP", "W", Units, 0, 0, Temperature1[i], Pressure1[i], WorkingFluidComposition).Output[0]
            SpeedOfSound2[i] = REFPROP.refprop(WorkingFluid, "TP", "W", Units, 0, 0, Temperature2[i], Pressure2[i], WorkingFluidComposition).Output[0]
            SpeedOfSound3[i] = REFPROP.refprop(WorkingFluid, "TP", "W", Units, 0, 0, Temperature3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            
            Viscosity1[i] = REFPROP.refprop(WorkingFluid, "TP", "Vis", Units, 0, 0, Temperature1[i], Pressure1[i], WorkingFluidComposition).Output[0]
            Viscosity2[i] = REFPROP.refprop(WorkingFluid, "TP", "Vis", Units, 0, 0, Temperature2[i], Pressure2[i], WorkingFluidComposition).Output[0]
            Viscosity3[i] = REFPROP.refprop(WorkingFluid, "TP", "Vis", Units, 0, 0, Temperature3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            
            AbsoluteVelocity3[i] = AbsoluteVelocity1 # (2*(TotalEnthalpy3[i]-Enthalpy3[i]))**0.5
            
            # if i <StageNumber -1:
            #     Enthalpy1[i+1] = Enthalpy3[i]
            #     Entropy1[i+1] = Entropy3[i]
            #     Pressure1[i+1] = Pressure3[i]
            #     Temperature1[i+1] = Temperature3[i]
            #     Density1[i+1] = Density3[i]
            
                # End of for loop for thermodynamic properties
            
            "_____________________________________________________________________________"
            "Geometric Parameters"
            "Rotor Geoemtry"
            TipDiameter1[i] = OuterDiameter*VarOutput[0]
            TipDiameterRatio[i] = VarOutput[0]
            HubDiameter1[i] = OuterDiameter*VarOutput[1]
            Diameter2[i] = OuterDiameter
            
            Volumeflow1[i] = InletVolumeflow*InletDensity/Density1[i]
            Volumeflow2[i] = InletVolumeflow*InletDensity/Density2[i]
            Volumeflow3[i] = InletVolumeflow*InletDensity/Density3[i]
            
            FlowArea1[i] = Volumeflow1[i]/AbsoluteMeridionalVelocity1
            FlowArea2[i] = Volumeflow2[i]/AbsoluteMeridionalVelocity2
            FlowArea3[i] = Volumeflow3[i]/AbsoluteVelocity3[i]
        
            BladeHeight2[i] = FlowArea2[i]/np.pi/Diameter2[i]
            HubDiameter1[i]= (TipDiameter1[i]**2-4*FlowArea1[i]/np.pi)**0.5
            BladeHeight1[i] = (TipDiameter1[i]-HubDiameter1[i])/2
            HubDiameterRatio[i] = HubDiameter1[i]/Diameter2[i]
            MeanDiameter1[i] = (TipDiameter1[i]+HubDiameter1[i])/2
            Alpha1MeanDiameter[i] = math.atan(math.tan(Alpha1)*TipDiameter1[i]/HubDiameter1[i])
            Beta1MeanDiameter[i] = math.atan(TipDiameterRatio[i]/FlowCoefficient*MeanDiameter1[i]/TipDiameter1[i]-math.tan(Alpha1MeanDiameter[i]))
            MeanRelativeVelocity1[i] = math.atan(1/(2*FlowCoefficient)*(TipDiameterRatio[i]+HubDiameterRatio[i])-(2*TipDiameterRatio[i]*math.tan(Alpha1))/(TipDiameter1[i]+HubDiameter1[i]))
            SlipFactor[i], Beta2Blade[i], RotorBladeNumber[i] = fsolve(SlipFunctionRotor, [0.9, Beta2, 10])
            RotorBladeNumber[i] = np.floor(RotorBladeNumber[i])
            Beta2Blade[i] = 2*math.acos(0.2*RotorBladeNumber[i]*math.log(1/TipDiameterRatio[i])/np.pi)-Beta1MeanDiameter[i]
            if Beta2Blade[i] > np.pi/2:     # Check to ensure the values of Beta2Blade do not cause errors in the calculation of the slip factor
                Beta2Blade[i] = np.pi/2
            SlipFactor[i] = 1-(math.cos(Beta2Blade[i]))**0.5/RotorBladeNumber[i]**0.7
            BetaMean[i] = (Beta1MeanDiameter[i]+Beta2Blade[i])/2
            RotorBladeThickness[i] = 0.01*Diameter2[i]  # For shrouded impellers
            AxialClearence[i] = 0.05*BladeHeight2[i]
            RadialClearence[i] = 0.05*BladeHeight2[i]
            BackfaceClearence[i] = 0.05*BladeHeight2[i]
            RotorInletBladePitch[i] = np.pi*MeanDiameter1[i]/RotorBladeNumber[i]
            RotorOutletBladePitch[i] = np.pi*Diameter2[i]/RotorBladeNumber[i]
            RotorInletBladeDistance[i] = RotorInletBladePitch[i]*math.cos(Beta1MeanDiameter[i])
            RotorOutletBladeDistance[i] = RotorOutletBladePitch[i]*math.cos(Beta2Blade[i])
            RotorInletCrossSection[i] = RotorInletBladeDistance[i]*BladeHeight1[i]
            RotorOutletCrossSection[i] = RotorOutletBladeDistance[i]*BladeHeight2[i]
            RotorInletWettedPerimeter[i] = 2*(RotorInletBladeDistance[i]+BladeHeight1[i])
            RotorOutletWettedPerimeter[i] = 2*(RotorOutletBladeDistance[i]+BladeHeight2[i])
            RotorInletHydraulicDiameter[i] =2*RotorInletBladeDistance[i]*BladeHeight1[i]/(RotorInletBladeDistance[i]+BladeHeight1[i])
            RotorOutletHydraulicDiameter[i] =2*RotorOutletBladeDistance[i]*BladeHeight2[i]/(RotorOutletBladeDistance[i]+BladeHeight2[i])
            RotorHydraulicDiameter[i] = (RotorInletHydraulicDiameter[i]+RotorOutletHydraulicDiameter[i])/2 
            RotorAxialLength[i] = Diameter2[i]*(0.014+0.023/HubDiameterRatio[i]+1.58*(TipDiameterRatio[i]**2-HubDiameterRatio[i]**2)*FlowCoefficient)
            RotorMeridionalLength[i] = np.pi/8*(2*RotorAxialLength[i]-BladeHeight2[i]+Diameter2[i]-TipDiameter1[i]+BladeHeight1[i])
            RotorHydraulicLength[i] = RotorMeridionalLength[i]/math.cos(BetaMean[i])
            
            "Stator Geometry"
            StatorAlpha2[i] = 72/180*np.pi+(Alpha2-72/180*np.pi)/4 if Alpha2 >= 72/180*np.pi else 72/180*np.pi
            StatorInletMachNumber = 1
            StatorDiameter2[i] = Diameter2[i]*(1+(np.pi/2-StatorAlpha2[i])/(2*np.pi)+StatorInletMachNumber**2/15)
            RotorOutletAbsoluteRotationalVelocity[i] = AbsoluteVelocity2*math.sin(Alpha2)
            StatorInletAbsoluteRotationalVelocity[i] = RotorOutletAbsoluteRotationalVelocity[i]*Diameter2[i]/StatorDiameter2[i]
            StatorInletAbsoluteMeridionalVelocity[i] = StatorInletAbsoluteRotationalVelocity[i]/math.tan(StatorAlpha2[i])
            StatorInletAbsoluteVelocity[i] = (StatorInletAbsoluteRotationalVelocity[i]**2+StatorInletAbsoluteMeridionalVelocity[i]**2)**0.5
            StatorInletBladeHeight[i] = Volumeflow2[i]/(StatorInletAbsoluteMeridionalVelocity[i]*np.pi*StatorDiameter2[i])
            StatorVanelessHydraulicLength[i] = (StatorDiameter2[i]-Diameter2[i])/2 
            StatorVanelessHydraulicDiameter[i] = BladeHeight2[i]+StatorInletBladeHeight[i]
            StatorOutletDiameter[i] = Diameter2[i]*(1.55+(TipDiameterRatio[i]**2-HubDiameterRatio[i]**2)*FlowCoefficient)
            StatorOutletBladeHeight[i] = StatorInletBladeHeight[i]
            StatorOutletAbsoluteMeridionalVelocity[i] = Volumeflow3[i]/(np.pi*StatorOutletDiameter[i]*StatorOutletBladeHeight[i])
            StatorOutletAbsoluteVelocity[i] = StatorOutletAbsoluteMeridionalVelocity[i]
            if RotorBladeNumber[i] <= 20:
                StatorBladeNumber[i] = RotorBladeNumber[i]-1
            else:
                StatorBladeNumber[i] = RotorBladeNumber[i]-8
            StatorVanedMeridionalLength[i] = (StatorOutletDiameter[i]-StatorDiameter2[i])/2
            StatorVanedHydraulicLength[i] = (StatorOutletDiameter[i]-StatorDiameter2[i])/(2*math.cos(StatorAlpha2[i]/2))
            StatorInletBladePitch[i] = np.pi*StatorDiameter2[i]/StatorBladeNumber[i]
            StatorOutletBladePitch[i] = np.pi*StatorOutletDiameter[i]/StatorBladeNumber[i]
            StatorSolidity[i] = (StatorOutletDiameter[i]-StatorDiameter2[i])/(2*StatorOutletBladePitch[i]*math.cos(StatorAlpha2[i]/2))
            StatorInletBladeDistance[i] = StatorInletBladePitch[i]*math.cos(StatorAlpha2[i])
            StatorOutletBladeDistance[i] = StatorOutletBladePitch[i]
            StatorInletCrossSection[i] = StatorInletBladeDistance[i]*StatorInletBladeHeight[i]
            StatorOutletCrossSection[i] = StatorOutletBladeDistance[i]*StatorOutletBladeHeight[i]
            StatorInletWettedPerimeter[i] = 2*(StatorInletBladeDistance[i]+StatorInletBladeHeight[i])
            StatorOutletWettedPerimeter[i] = 2*(StatorOutletBladeDistance[i]+StatorOutletBladeHeight[i])
            StatorVanedInletHydraulicDiameter[i] = 2*((StatorInletBladeDistance[i]*StatorInletBladeHeight[i]))/(StatorInletBladeDistance[i]+StatorInletBladeHeight[i])
            StatorVanedOutletHydraulicDiameter[i] = 2*((StatorOutletBladeDistance[i]*StatorOutletBladeHeight[i]))/(StatorOutletBladeDistance[i]+StatorOutletBladeHeight[i])
            StatorVanedHydraulicDiameter[i] = (StatorVanedInletHydraulicDiameter[i]+StatorVanedOutletHydraulicDiameter[i])/2
            
            RotorInletReynoldsNumber[i] = Density1[i]*RelativeVelocity1*RotorHydraulicDiameter[i]/Viscosity1[i]
            RotorOutletReynoldsNumber[i] = Density2[i]*RelativeVelocity2*RotorHydraulicDiameter[i]/Viscosity2[i]
            StatorInletReynoldsNumber[i] = Density2[i]*AbsoluteVelocity2*StatorVanedHydraulicDiameter[i]/Viscosity2[i]
            StatorOutletReynoldsNumber[i] = Density3[i]*AbsoluteVelocity3[i]*StatorVanedHydraulicDiameter[i]/Viscosity3[i]
            
            RotorRoughness[i] = RotorHydraulicDiameter[i]*100/RotorInletReynoldsNumber[i]
            StatorRoughness[i] = StatorVanedHydraulicDiameter[i]*100/StatorInletReynoldsNumber[i]
            
            StatorBladeThickness[i] = 0.01*Diameter2[i]
            
            "_____________________________________________________________________________"
            "Losses"
            "Rotor Losses"
            # Incidence Loss
            IncidenceLossCoefficient[i] = (RotorBladeNumber[i]*RotorBladeThickness[i]/(np.pi*MeanDiameter1[i]*math.cos(Beta1MeanDiameter[i])))**2
            MeanRelativeVelocity1[i] = AbsoluteMeridionalVelocity1/math.cos(Beta1MeanDiameter[i])
            # Skin Friction Loss
            MeanRelativeVelocity[i] = ((MeanRelativeVelocity1[i]**2+RelativeVelocity2**2)/2)**0.5
            RotorSkinFrictionReynoldsNumber[i] = Density1[i]*MeanRelativeVelocity1[i]*RotorHydraulicDiameter[i]/Viscosity1[i]
            if RotorSkinFrictionReynoldsNumber[i] < 2000:
                RotorSkinFrictionCoefficient[i] = 16/RotorSkinFrictionReynoldsNumber[i]
            elif RotorSkinFrictionReynoldsNumber[i] > 4000:
                RotorSkinFrictionCoefficientSmooth[i] = fsolve(SkinFrictionFunctionRotor, 0.001)
                RotorSkinFrictionCoefficientRough[i] = (1/(-4*math.log10(1/3.71*RotorRoughness[i]/RotorHydraulicDiameter[i])))**2
                RotorSkinFrictionRoughReynoldsNumber[i] = (RotorSkinFrictionReynoldsNumber[i]-2000)*RotorRoughness[i]/RotorHydraulicDiameter[i]
                if RotorSkinFrictionRoughReynoldsNumber[i] < 60:
                    RotorSkinFrictionCoefficient[i] = RotorSkinFrictionCoefficientSmooth[i]
                else:
                    RotorSkinFrictionCoefficient[i] = RotorSkinFrictionCoefficientSmooth[i]+(RotorSkinFrictionCoefficientRough[i]-RotorSkinFrictionCoefficientSmooth[i])*(1-60/RotorSkinFrictionRoughReynoldsNumber[i])
            else:
                RotorSkinFrictionRoughReynoldsNumber[i] = (4000-2000)*RotorRoughness[i]/RotorHydraulicDiameter[i]
                if RotorSkinFrictionRoughReynoldsNumber[i] < 60:
                    RotorSkinFrictionCoefficient4000 = fsolve(SkinFrictionFunctionRotor4000, 0.001)
                else:
                    RotorSkinFrictionCoefficientSmooth4000 = fsolve(SkinFrictionFunctionRotor4000, 0.001)
                    RotorSkinFrictionCoefficientRough4000 = (1/(-4*math.log10(1/3.71*RotorRoughness/RotorHydraulicDiameter)))**2
                    RotorSkinFrictionCoefficient4000 = RotorSkinFrictionCoefficientSmooth4000[i]+(RotorSkinFrictionCoefficientRough4000[i]-RotorSkinFrictionCoefficientSmooth4000[i])*(1-60/RotorSkinFrictionRoughReynoldsNumber[i])
                RotorSkinFrictionCoefficient[i] = 16/2000-(16/2000-RotorSkinFrictionCoefficient4000)*(RotorSkinFrictionReynoldsNumber/2000-1)
            RotorSkinFrictionLossCoefficient[i] = 4*RotorSkinFrictionCoefficient[i]*RotorHydraulicLength[i]/RotorHydraulicDiameter[i]*(MeanRelativeVelocity[i]/MeanRelativeVelocity1[i])**2
            # Blade Loading Loss
            BladeLoadingLossCoefficient[i] = 1/24*(2*np.pi*Diameter2[i]*RotationalVelocity2*WorkCoefficient/(RotorBladeNumber[i]*RotorHydraulicLength[i]*MeanRelativeVelocity1[i]))**2
            # Hub to Shroud Losses
            Km[i] = np.pi/2*RotorHydraulicLength[i]
            MeanBladeHeight[i] = (BladeHeight1[i]+BladeHeight2[i])/2
            MeanRelativeVelocityAlt[i] = (MeanRelativeVelocity1[i]+RelativeVelocity2)/2
            HubToShroudLossCoefficient[i] = 1/6*(Km[i]*MeanBladeHeight[i]*MeanRelativeVelocityAlt[i]/MeanRelativeVelocity1[i])**2
            # Mixing Losses
            EquivalentDiffusionFactor[i] = (MeanRelativeVelocity1[i]+RelativeVelocity2+2*np.pi*Diameter2[i]*RotationalVelocity2*WorkCoefficient/(RotorBladeNumber[i]*RotorHydraulicLength[i]))/(2*RelativeVelocity2)
            if EquivalentDiffusionFactor[i] <= 2:
                SeperationVelocity[i] = RelativeVelocity2
            else:
                SeperationVelocity[i] = RelativeVelocity2*EquivalentDiffusionFactor[i]/2
            AbsoluteMeridionalMixingVelocity[i] = AbsoluteMeridionalVelocity2*(1-RotorBladeNumber[i]*RotorBladeThickness[i]/(np.pi*Diameter2[i]))
            AbsoluteMeridionalWakeVelocity[i] = (SeperationVelocity[i]**2-RelativeRotationalVelocity2**2)**0.5
            MixingLossCoefficient[i] = ((AbsoluteMeridionalWakeVelocity[i]-AbsoluteMeridionalMixingVelocity[i])/MeanRelativeVelocity1[i])**2
            # Clearence Losses (only for open impellers, will be implemented at a later time)
            ClearenceLossCoefficient[i] = 0
            
            RotorLossCoefficient[i] = (IncidenceLossCoefficient[i]+RotorSkinFrictionLossCoefficient[i]+BladeLoadingLossCoefficient[i]+HubToShroudLossCoefficient[i]+MixingLossCoefficient[i]+ClearenceLossCoefficient[i])
            
            "Stator Losses"
            # Vaneless Diffuser
            AbsoluteQuadraticMeanVelocity[i] = ((StatorInletAbsoluteVelocity[i]**2+AbsoluteVelocity2**2)/2)**0.5
            DivergenceParameter[i] = BladeHeight2[i]*(StatorDiameter2[i]/Diameter2[i]-1)/StatorVanelessHydraulicLength[i]
            ReferenceParameter[i] = 0.4*(BladeHeight2[i]/StatorVanelessHydraulicLength[i])**0.35
            if DivergenceParameter[i] <= 0:
                DiffusionEfficiency[i] = 1
            elif DivergenceParameter[i] < ReferenceParameter[i]:
                DiffusionEfficiency[i] = 1-0.2*(DivergenceParameter[i]/ReferenceParameter[i])**2
            else:
                DiffusionEfficiency[i] = 0.8*(ReferenceParameter[i]/DivergenceParameter[i])**0.5
            StatorVanelessDiffusionLossCoefficient[i] = -2*(1-DiffusionEfficiency[i])*(StatorInletAbsoluteVelocity[i]-AbsoluteVelocity2)/AbsoluteVelocity2
            
            StatorVanelessSkinFrictionReynoldsNumber[i] = Density2[i]*RelativeVelocity2*StatorVanelessHydraulicDiameter[i]/Viscosity2[i]
            if StatorVanelessSkinFrictionReynoldsNumber[i] < 2000:
                StatorVanelessSkinFrictionCoefficient[i] = 16/StatorVanelessSkinFrictionReynoldsNumber[i]
            elif StatorVanelessSkinFrictionReynoldsNumber[i] > 4000:
                StatorVanelessSkinFrictionCoefficientSmooth[i] = fsolve(SkinFrictionFunctionStatorVaneless, 0.001)
                StatorVanelessSkinFrictionCoefficientRough[i] = (1/(-4*math.log10(1/3.71*StatorRoughness[i]/StatorVanelessHydraulicDiameter[i])))**2
                StatorVanelessSkinFrictionRoughReynoldsNumber[i] = (StatorVanelessSkinFrictionReynoldsNumber[i]-2000)*StatorRoughness[i]/StatorVanelessHydraulicDiameter[i]
                if StatorVanelessSkinFrictionRoughReynoldsNumber[i] < 60:
                    StatorVanelessSkinFrictionCoefficient[i] = StatorVanelessSkinFrictionCoefficientSmooth[i]
                else:
                    StatorVanelessSkinFrictionCoefficient[i] = StatorVanelessSkinFrictionCoefficientSmooth[i]+(StatorVanelessSkinFrictionCoefficientRough[i]-StatorVanelessSkinFrictionCoefficientSmooth[i])*(1-60/StatorVanelessSkinFrictionRoughReynoldsNumber[i])
            else:
                StatorVanelessSkinFrictionRoughReynoldsNumber[i] = (4000-2000)*StatorRoughness[i]/StatorVanelessHydraulicDiameter[i]
                if StatorVanelessSkinFrictionRoughReynoldsNumber[i] < 60:
                    StatorVanelessSkinFrictionCoefficient4000 = fsolve(SkinFrictionFunctionStatorVaneless4000, 0.001)
                else:
                    StatorVanelessSkinFrictionCoefficientSmooth4000 = fsolve(SkinFrictionFunctionStatorVaneless4000, 0.001)
                    StatorVanelessSkinFrictionCoefficientRough4000 = (1/(-4*math.log10(1/3.71*StatorRoughness[i]/StatorVanelessHydraulicDiameter[i])))**2
                    StatorVanelessSkinFrictionCoefficient4000 = StatorVanelessSkinFrictionCoefficientSmooth4000[i]+(StatorVanelessSkinFrictionCoefficientRough4000[i]-StatorVanelessSkinFrictionCoefficientSmooth4000[i])*(1-60/StatorVanelessSkinFrictionRoughReynoldsNumber[i])
                StatorVanelessSkinFrictionCoefficient[i] = 16/2000-(16/2000-StatorVanelessSkinFrictionCoefficient4000)*(StatorVanelessSkinFrictionReynoldsNumber/2000-1)
            StatorVanelessSkinFrictionLossCoefficient[i] = 4*StatorVanelessSkinFrictionCoefficient[i]*StatorVanelessHydraulicLength[i]/StatorVanelessHydraulicDiameter[i]*(MeanRelativeVelocity[i]/MeanRelativeVelocity1[i])**2
            
            StatorVanelessLossCoefficient[i] = (StatorVanelessDiffusionLossCoefficient[i]+StatorVanelessSkinFrictionLossCoefficient[i])
            
            # Vaned Diffuser
            StatorVanedIncidenceLossCoefficient[i] = 0.8*(1-StatorInletAbsoluteMeridionalVelocity[i]/(StatorInletAbsoluteVelocity[i]*math.cos(StatorAlpha2[i])))**2+(StatorBladeNumber[i]*StatorBladeThickness[i]/(np.pi*StatorDiameter2[i]))**2
            AbsoluteMeridionalMixingVelocity3[i] = StatorOutletAbsoluteMeridionalVelocity[i]*(1-StatorBladeNumber[i]*StatorBladeThickness[i]/(np.pi*StatorOutletDiameter[i]))
            StatorEquivalentDiffusionFactor[i] = StatorInletAbsoluteVelocity[i]/StatorOutletAbsoluteVelocity[i]
            if StatorEquivalentDiffusionFactor[i] <= 2:
                SeperationVelocity3[i] = StatorOutletAbsoluteVelocity[i]
            else:
                SeperationVelocity3[i] = StatorOutletAbsoluteVelocity[i]*StatorEquivalentDiffusionFactor[i]/2
            AbsoluteMeridionalWakeVelocity3[i] = (SeperationVelocity3[i]**2-StatorOutletAbsoluteVelocity[i]**2)**0.5
            StatorVanedMixingLossCoefficient[i] = ((AbsoluteMeridionalWakeVelocity3[i]-AbsoluteMeridionalMixingVelocity3[i])/StatorInletAbsoluteVelocity[i])**2
            
            StatorVanedSkinFrictionReynoldsNumber[i] = Density2[i]*StatorInletAbsoluteVelocity[i]*StatorVanedHydraulicDiameter[i]/Viscosity2[i]
            if StatorVanedSkinFrictionReynoldsNumber[i] < 2000:
                StatorVanedSkinFrictionCoefficient[i] = 16/StatorVanedSkinFrictionReynoldsNumber[i]
            elif StatorVanedSkinFrictionReynoldsNumber[i] > 4000:
                StatorVanedSkinFrictionCoefficientSmooth[i] = fsolve(SkinFrictionFunctionStatorVaned, 0.001)
                StatorVanedSkinFrictionCoefficientRough[i] = (1/(-4*math.log10(1/3.71*StatorRoughness[i]/StatorVanedHydraulicDiameter[i])))**2
                StatorVanedSkinFrictionRoughReynoldsNumber[i] = (StatorVanedSkinFrictionReynoldsNumber[i]-2000)*StatorRoughness[i]/StatorVanedHydraulicDiameter[i]
                if StatorVanedSkinFrictionRoughReynoldsNumber[i] < 60:
                    StatorVanedSkinFrictionCoefficient[i] = StatorVanedSkinFrictionCoefficientSmooth[i]
                else:
                    StatorVanedSkinFrictionCoefficient[i] = StatorVanedSkinFrictionCoefficientSmooth[i]+(StatorVanedSkinFrictionCoefficientRough[i]-StatorVanedSkinFrictionCoefficientSmooth[i])*(1-60/StatorVanedSkinFrictionRoughReynoldsNumber[i])
            else:
                StatorVanedSkinFrictionRoughReynoldsNumber[i] = (4000-2000)*StatorRoughness[i]/StatorVanedHydraulicDiameter
                if StatorVanedSkinFrictionRoughReynoldsNumber[i] < 60:
                    StatorVanedSkinFrictionCoefficient4000 = fsolve(SkinFrictionFunctionStatorVaned4000, 0.001)
                else:
                    StatorVanedSkinFrictionCoefficientSmooth4000 = fsolve(SkinFrictionFunctionStatorVaned4000, 0.001)
                    StatorVanedSkinFrictionCoefficientRough4000 = (1/(-4*math.log10(1/3.71*StatorRoughness/StatorVanedHydraulicDiameter)))**2
                    StatorVanedSkinFrictionCoefficient4000 = StatorVanedSkinFrictionCoefficientSmooth4000[i]+(StatorVanedSkinFrictionCoefficientRough4000[i]-StatorVanedSkinFrictionCoefficientSmooth4000[i])*(1-60/StatorVanedSkinFrictionRoughReynoldsNumber[i])
                StatorVanedSkinFrictionCoefficient[i] = 16/2000-(16/2000-StatorVanedSkinFrictionCoefficient4000)*(StatorVanedSkinFrictionReynoldsNumber/2000-1)
            A[i] = (5.142*StatorVanedSkinFrictionCoefficient[i]*StatorVanedHydraulicLength[i]/StatorVanedHydraulicDiameter[i])**0.25
            StatorVanedSkinFrictionLossCoefficient[i] = 4*StatorVanedSkinFrictionCoefficient[i]/A[i]*StatorVanedHydraulicLength[i]/StatorVanedHydraulicDiameter[i]*(AbsoluteQuadraticMeanVelocity[i]/StatorInletAbsoluteVelocity[i])**2
            
            StatorVanedLossCoefficient[i] = (StatorVanedIncidenceLossCoefficient[i]+StatorVanedMixingLossCoefficient[i]+StatorVanedSkinFrictionLossCoefficient[i])
            
            StatorLossCoefficient[i] = (StatorVanelessLossCoefficient[i]+StatorVanedLossCoefficient[i])
            
            
            "_____________________________________________________________________________"
            "Efficiency Calculations"
            IsentropicTotalRelativeEnthalpy2[i] = TotalRelativeEnthalpy2[i]  # IsentropicEnthalpy2[i]+RelativeVelocity2**2/2 
            IsentropicTotalRelativePressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, IsentropicTotalRelativeEnthalpy2[i], Entropy1[i], WorkingFluidComposition).Output[0]
            LossTotalRelativePressure2[i] = IsentropicTotalRelativePressure2[i]/(1+RotorLossCoefficient[i]*(1-Pressure1[i]/TotalRelativePressure1[i]))
            LossEntropy2[i] = REFPROP.refprop(WorkingFluid, "HP", "S", Units, 0, 0, TotalRelativeEnthalpy2[i], LossTotalRelativePressure2[i], WorkingFluidComposition).Output[0]
            LossEnthalpy2[i] = REFPROP.refprop(WorkingFluid, "SP", "H", Units, 0, 0, LossEntropy2[i], Pressure2[i], WorkingFluidComposition).Output[0]
            RotorEfficiency[i] = (IsentropicEnthalpy2[i]-Enthalpy1[i])/(LossEnthalpy2[i]-Enthalpy1[i])
            LossTotalEnthalpy2[i] = LossEnthalpy2[i]+AbsoluteVelocity2**2/2 
            LossTotalPressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, LossTotalEnthalpy2[i], LossEntropy2[i], WorkingFluidComposition).Output[0]
            LossPressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, LossEnthalpy2[i], LossEntropy2[i], WorkingFluidComposition).Output[0]
            LossStatorInletTotalPressure2[i] = LossTotalPressure2[i]-StatorVanelessLossCoefficient[i]*(LossTotalPressure2[i]-LossPressure2[i])
            LossTotalPressure3[i] = LossStatorInletTotalPressure2[i]-StatorVanedLossCoefficient[i]*(LossStatorInletTotalPressure2[i]-LossPressure2[i])
            LossTotalEnthalpy3[i] = LossTotalEnthalpy2[i]
            LossEntropy3[i] = REFPROP.refprop(WorkingFluid, "HP", "S", Units, 0, 0, LossTotalEnthalpy3[i], LossTotalPressure3[i], WorkingFluidComposition).Output[0]
            LossEnthalpy3[i] = REFPROP.refprop(WorkingFluid, "SP", "H", Units, 0, 0, LossEntropy3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            LossTotalEnthalpy3[i] = LossEnthalpy3[i]+AbsoluteVelocity3[i]**2/2 
            TotalEfficiency[i] = ((IsentropicEnthalpy3[i]+AbsoluteVelocity3[i]**2/2)-TotalEnthalpy1[i])/(LossTotalEnthalpy3[i]-TotalEnthalpy1[i])
            IsentropicEfficiency[i] = (IsentropicEnthalpy3[i]-Enthalpy1[i])/(LossEnthalpy3[i]-Enthalpy1[i])
            StaticEfficiency[i] = (IsentropicEnthalpy3[i]-TotalEnthalpy1[i])/(LossTotalEnthalpy3[i]-TotalEnthalpy1[i])
            StatorEfficiency[i] = (IsentropicEnthalpy3[i]-LossEnthalpy2[i])/(LossEnthalpy3[i]-LossEnthalpy2[i])
        
            "Thermodynamic Inlet Conditions of the following Stage"
            if i <StageNumber -1:
                Enthalpy1[i+1] = LossEnthalpy3[i]+AbsoluteVelocity3[i]**2/2-AbsoluteVelocity1**2/2 
                Entropy1[i+1] = LossEntropy3[i]
                Pressure1[i+1] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, LossEnthalpy3[i], LossEntropy3[i], WorkingFluidComposition).Output[0]
                Temperature1[i+1] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, LossEnthalpy3[i], LossEntropy3[i], WorkingFluidComposition).Output[0]
                Density1[i+1] = REFPROP.refprop(WorkingFluid, "HS", "D", Units, 0, 0, LossEnthalpy3[i], LossEntropy3[i], WorkingFluidComposition).Output[0]
                
            "Loss based Properties"
            LossTemperature2[i] = REFPROP.refprop(WorkingFluid, "HS", "T", Units, 0, 0, LossEnthalpy2[i], LossEntropy2[i], WorkingFluidComposition).Output[0]
            LossTemperature3[i] = REFPROP.refprop(WorkingFluid, "HP", "T", Units, 0, 0, LossEnthalpy3[i], Pressure3[i], WorkingFluidComposition).Output[0]
            LossPressure2[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, LossEnthalpy2[i], LossEntropy2[i], WorkingFluidComposition).Output[0]
            LossPressure3[i] = REFPROP.refprop(WorkingFluid, "HS", "P", Units, 0, 0, LossEnthalpy3[i], LossEntropy3[i], WorkingFluidComposition).Output[0]
            
            # End of the loop over the stages
        EstimatedIsentropicRotorEfficiency= RotorEfficiency
        OverallEstimatedIsentropicEfficiency = (IsentropicOutletEnthalpy-InletEnthalpy)/((LossEnthalpy3[StageNumber-1]-InletEnthalpy))
        # if OverallEstimatedIsentropicEfficiency <= 0:       # Check to ensure that value is physically feasible for next iteration step
        #     OverallEstimatedIsentropicEfficiency = 1
        # print("Estimation")
        # print(OverallEstimatedIsentropicEfficiency)
        CalculatedIsentropicEfficiency[j] = OverallEstimatedIsentropicEfficiency
        
        "Losses and Efficiency"
        # fig, axs = plt.subplots(1, 2, figsize=(15, 10))
        # fig.suptitle('Losses and Efficiency')
        # x = np.array(range(StageNumber))+1
        # axs[0].plot(x, RotorLossCoefficient, 'x-', label='Rotor')
        # axs[0].plot(x, StatorLossCoefficient, 'x-', label='Stator')
        # axs[0].set_title('Loss Coefficients')
        # axs[0].set_xlabel('Stage Number')
        # axs[0].set_ylabel('Loss Coefficients')
        # axs[0].legend()
    
        # axs[1].plot(x, IsentropicEfficiency, 'x-', label='Isentropic')
        # axs[1].plot(x, StaticEfficiency, 'x-', label='Static')
        # axs[1].plot(x, TotalEfficiency, 'x-', label='Total')
        # axs[1].plot(x, RotorEfficiency, 'x-', label='Rotor')
        # axs[1].set_title('Efficiencies')
        # axs[1].set_xlabel('Stage Number')
        # axs[1].set_ylabel('Efficiency')
        # axs[1].legend()
    
        # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        # plt.show()
        # End of the loop redoing the calculations
        
    "_____________________________________________________________________________"
    "Machine Results"
    OverallIsentropicEfficiency = (IsentropicOutletEnthalpy-InletEnthalpy)/((LossEnthalpy3[StageNumber-1]-InletEnthalpy))
    OverallTotalEfficiency = (IsentropicOutletEnthalpy+AbsoluteVelocity3**2/2-InletEnthalpy-AbsoluteVelocity1**2/2)/((LossTotalEnthalpy3[StageNumber-1]-InletEnthalpy-AbsoluteVelocity1**2/2))
    OverallStaticEfficiency = (IsentropicOutletEnthalpy-InletEnthalpy-AbsoluteVelocity1**2/2)/((LossTotalEnthalpy3[StageNumber-1]-InletEnthalpy-AbsoluteVelocity1**2/2))
    # print("Isentropic Efficiency")
    # print(OverallIsentropicEfficiency)
    
    ResultDictionary = {"Isentropic Efficiency": OverallIsentropicEfficiency,
                        "Total Efficiency": OverallTotalEfficiency,
                        "Static Efficiency": OverallStaticEfficiency,
                        "Inlet Tip Diameter": TipDiameter1,
                        "Inlet Hub Diameter": HubDiameter1,
                        "Rotor Outlet Diameter": Diameter2,
                        "Stator Inlet Diameter": StatorDiameter2,
                        "Stator Outlet Diameter": StatorOutletDiameter,
                        "Rotor Blade Number": RotorBladeNumber,
                        "Stator Blade Number": StatorBladeNumber,
                        "Rotor Axial Lenght": RotorAxialLength,
                        "Inlet Velocity": AbsoluteVelocity1,
                        "Outlet Velocity": AbsoluteVelocity3[StageNumber-1],
                        "Outlet Temperature": Temperature3[StageNumber-1],
                        "Outlet Pressure": Pressure3[StageNumber-1],
                        "Outlet Enthalpy": Enthalpy3[StageNumber-1],
                        "Outlet Entropy": Entropy3[StageNumber-1],
                        "Outlet Density": Density3[StageNumber-1],
                        "Stage Number": StageNumber,
                        "Work Coefficient": WorkCoefficient,
                        "Flow Coefficient": FlowCoefficient,
                        "Specific Speed": SpecificSpeed,
                        "Specific Diameter": SpecificDiameter}


    return ResultDictionary