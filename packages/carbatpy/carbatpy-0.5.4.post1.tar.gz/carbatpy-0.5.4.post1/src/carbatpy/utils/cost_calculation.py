# -*- coding: utf-8 -*-
"""
Calculating costs for equipment

SI units input is only implemented for the Towler method and the limits are
checked now for Towler! (BA 2025-08-14/15)

Created on Wed Jul 31 13:59:25 2024

@author: Mina Anton
"""

import numpy as np
import pandas as pd
import datetime
import sys
import warnings
import carbatpy as cb


# Pfad zur Excel-Datei
DIR = cb.CB_DEFAULTS["General"]['CB_DATA']
_EXCEL_FILE = DIR + "\\" + "Capital_Investment_Methods_ba.xlsx"

# Speicherstrukturen: Dict mit {sheetname: {"columns": [...], "values": np.array([...])}}
_CAP_DATA = {}

try:
    xl_data = pd.ExcelFile(_EXCEL_FILE, engine="openpyxl")

    for sheet in ["Couper Method", "Turton Method", "Towler Method", "CEPCI data"]:
        df = xl_data.parse(sheet)
        _CAP_DATA[sheet] = {
            "columns": list(df.columns),
            "values": df.values,
            "df": df,
        }
    cols = _CAP_DATA["Towler Method"]["columns"]
    _Towler_unit_col_indices = [
        i for i, col in enumerate(cols)
        if str(col).lower().startswith("unit")]

except Exception as e:
    print(f"Error loading Excel file: {e}")


class CAP_methods:
    def __init__(self):

        # Direktes Zuweisen der vorbereiteten Daten
        self.Couper_columns = _CAP_DATA["Couper Method"]["columns"]
        self.Couper_xl_data = _CAP_DATA["Couper Method"]["values"]

        self.Turton_columns = _CAP_DATA["Turton Method"]["columns"]
        self.Turton_xl_data = _CAP_DATA["Turton Method"]["values"]

        self.Towler_columns = _CAP_DATA["Towler Method"]["columns"]
        self.Towler_xl_data = _CAP_DATA["Towler Method"]["values"]
        self.Towler_df = _CAP_DATA["Towler Method"]["df"]
        self.Towler_unit_col_index = _Towler_unit_col_indices[0]

        self.CEPCI_columns = _CAP_DATA["CEPCI data"]["columns"]
        self.CEPCI_xl_data = _CAP_DATA["CEPCI data"]["values"]
        self.warn = {'value': 0,
                     'message': 'All o.k.'}

    def _Find_Present_Cost(self, BaseCost, BaseYear, plot=False, Current_year=True, Desired_year=None):
        """
        Function used to adjust the cost of a component to the present day, accounting for inflation. It uses the
        CEPCI (Chemical Engineering cost index data).

        Parameters
        ----------
        BaseCost : TYPE, Float.
            DESCRIPTION: Cost of the compoenent based on the year the correlation is published.
        BaseYear : TYPE, Float.
            DESCRIPTION: Year the correlation for the cost estimate is published.
        plot : TYPE, optional.
            DESCRIPTION. The default is True. Plots the CEPCI vs year.
        Current_year : TYPE, Boolean, optional.
            DESCRIPTION : The default is True. Should the CEPCI cost index be taken relative to the current year.
        Desired_year : TYPE, Float, optional.
            DESCRIPTION : The default is None. If you choose False for Current_year, what year do you want
            the cost index to be relative to.

        Returns
        -------
        costPresent : TYPE, Float.
            DESCRIPTION: Present day cost of the component, accounting for inflation.

        """

        # Finds the year for todays date
        if Current_year == True:
            year = datetime.datetime.now().year
        else:
            if Desired_year is not None:
                year = Desired_year
            else:
                raise ValueError(
                    "Desired year is not provided although Current year was set to False")

        # Find the current and past cost index for the component
        if year in self.CEPCI_xl_data[:, 0]:
            index_present = self.CEPCI_xl_data[np.where(
                self.CEPCI_xl_data[:, 0] == year), 1]
            index_data = self.CEPCI_xl_data[np.where(
                self.CEPCI_xl_data[:, 0] == BaseYear), 1]
        # Check if present date has a cost index in CECPI
        else:
            print("\nerror: no cost index data for ", year)
            sys.exit()

        if plot:
            print("\ncost index ratio: ", index_present[0][0], "/", index_data[0]
                  [0], " = ", np.round((index_present/index_data)[0][0], 2), "\n")

        costPresent = float(BaseCost*(index_present[0][0]/index_data[0][0]))

        return costPresent

    def _Couper_Method(self, Comp_dict, verbose=False, Desired_year=None):
        """
        Method based on cost estimation techniques for indivisual components
        from chapter 21 in Chemical Process
        Equipment, Third Edition (2012).
        
        SI-unit input not implemented yet! Limits are not checked! BA 2025-08-15

        Parameters
        ----------
        Comp_dict : TYPE, Dictionary.
            DESCRIPTION : This dictionary contains all the variables and paramters needed to
            find a cost estimate for a particular component. For the exact values in the dictionary
            check the excel file Capital_Investment_Methods or read chapter 21 in Chemical Process
            Equipment, Third Edition (2012).
            Comp_dict_example = {
            "Category": ,
            "Component Name": ,
            "Power" :,      # For the turton method the pressures are in guage, 100 KPa = 1atm
            "Area": ,
            "Pressure": ,
            "Volume": ,
            "Volume Flow Rate": ,
            "Head":
                }
        verbose : TYPE, Boolean, optional.
            DESCRIPTION : should values be printed along with an explanation?
        Desired_year : TYPE, Float, optional.
            DESCRIPTION : The default is None. Do you want the cost index to be taken relative to the current year or another previous years?
            If you want the cost index to be taken relative to a previuos year, input value to Desired_year.

        Raises
        ------
        ValueError.
            DESCRIPTION : Checks if the component name is available in the Couper method excel sheet.

        Returns
        -------
        TYPE, String.
            DESCRIPTION : The installed cost of the component, adjusted to present day to account
            for inflation. This cost estimate also accounts for operational pressure and material of construction.

        """

        self.Component_category = Comp_dict.get("Category")
        self.Component_name = Comp_dict.get("Component Name")
        self.Power = Comp_dict.get("Power")
        self.Area = Comp_dict.get("Area")
        self.Pressure = Comp_dict.get("Pressure")
        self.Volume = Comp_dict.get("Volume")
        self.Q = Comp_dict.get("Volume Flow Rate")
        self.h = Comp_dict.get("Head")

        # Finds row corresponding to component and checks if component is available in this method
        index = np.where(self.Couper_xl_data[:, 1] == self.Component_name)[0]
        if index.size == 0:
            raise ValueError(
                "Component name is not found in the Couper method")

        # Array index contains the row for the component
        # Finds values needed for the cost estimation for the component
        Component_row = self.Couper_xl_data[index[0]]
        a = float(Component_row[2])
        b1 = float(Component_row[3])
        b2 = float(Component_row[4])
        b3 = float(Component_row[5])
        n = float(Component_row[6])
        iF = float(Component_row[7])
        fm = float(Component_row[8])
        ccF = float(Component_row[9])
        cF = float(Component_row[13])
        cF2 = float(Component_row[17])
        yr = float(Component_row[18])
        fd = None
        fp = None

        # Calculate cost of compressor
        if self.Component_category == "Compressor":

            HP = self.Power * cF
            CI = a * (HP**n) * iF * ccF * 1000
            CI = self._Find_Present_Cost(CI, yr, plot=False, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Power} KW. The price of the component using Couper Method : {CI} euro")

            return float(CI)

        # Calculate cost of turbines
        elif self.Component_category == "Turbine":

            HP = self.Power * cF
            CI = a * (HP**n) * iF * ccF * 1000
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Power} KW. The price of the component using Couper Method : {CI} euro ")

            return float(CI)

        # Calculate cost of shell and tube heat exchangers
        elif self.Component_category == "Heat Exchanger S/T":

            Area_sqft = self.Area * cF

            if "Shell and Tube, Fixed Head" in self.Component_name:
                fd = np.exp(-1.1156 + 0.0906 * np.log(Area_sqft))
            elif "Shell and Tube, Kettle Reboiler" in self.Component_name:
                fd = 1.35
            elif "Shell and Tube, U Tube" in self.Component_name:
                fd = np.exp(-0.9816 + 0.0830 * np.log(Area_sqft))

            if 689.476 <= self.Pressure <= 2068.43:
                fp = 0.7771 + 0.04981 * np.log(Area_sqft)
            elif 2068.43 < self.Pressure <= 4136.85:
                fp = 1.0305 + 0.07140 * np.log(Area_sqft)
            elif 4136.85 < self.Pressure <= 6205.28:
                fp = 1.1400 + 0.12088 * np.log(Area_sqft)
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Couper method")

            Fm = b1 + b2 * np.log(Area_sqft)
            Cb = np.exp(8.821 - 0.30863 * np.log(Area_sqft) +
                        0.0681 * (np.log(Area_sqft) ** n))
            CI = a * fd * Fm * fp * Cb * ccF * iF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Pressure} KPa and {self.Area} m^2. The price of the component using Couper Method : {CI} euro ")

            return float(CI)

        # Calculate cost of double pipe heat exchnagers
        elif self.Component_category == "Heat Exchanger D/P":

            Area_sqft = self.Area * cF

            if self.Pressure <= 400:
                fp = 1
            elif 400 < self.Pressure <= 600:
                fp = 1.10
            elif 600 < self.Pressure <= 700:
                fp = 1.25
            else:
                print(
                    "The operational pressure for the double pipe heat exchanger is out of range for the Couper method")

            CI = a * fm * fp * Area_sqft**n
            CI = CI * iF * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Pressure} KPa and {self.Area} m^2. The price of the component using Couper Method : {CI} euro ")

            return float(CI)

        # Calculate cost of storage tanks
        elif self.Component_category == "Shop Fabricated Storage Tank":

            Volume_gal = self.Volume * cF
            CI = a * fm * \
                np.exp(2.631 + 1.3673 * np.log(Volume_gal) -
                       0.06309 * (np.log(Volume_gal))**n)
            CI = CI * iF * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Volume} m^3. The price of the component using Couper Method : {CI} euro")

            return float(CI)

        # Calculate cost of centrifugal pumps
        elif self.Component_category == "VSC Centrifugal Pump" or self.Component_category == "HSC Centrifugal Pump":

            Q_gpm = self.Q * cF
            h_ft = self.h * cF2
            Cb = 3.00 * np.exp(8.833 - 0.6019 * np.log(Q_gpm * np.sqrt(h_ft)
                                                       ) + 0.0519 * (np.log(Q_gpm * np.sqrt(h_ft)))**n)
            ft = np.exp(b1 + b2 * np.log(Q_gpm * np.sqrt(h_ft)) +
                        b3 * np.log(Q_gpm * np.sqrt(h_ft))**n)
            CI = fm * ft * Cb * ccF * iF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Q} m^3/s and {self.h} m. The price of the component using Couper Method : {CI} euro ")

            return float(CI)

        # Calculate cost of recipocating pumps
        elif self.Component_category == "Pump":
            print(
                "The costs produced for Reciprocating pumps using Couper Methods are unexpectedly high")
            Q_gpm = self.Q * cF
            CI = a * fm * (Q_gpm**n)
            CI = CI * iF * ccF * 1000
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.Q} m^3/s. The price of the component using Couper Method : {CI} euro ")

            return float(CI)

    def Towler_Method(self, Comp_dict, verbose=False, Desired_year=None):
        """
        Cost estimation according to:

        Towler and Gavin (2012)
        "Chemical engineering design: principles, practice and economics of plant and process design".
        
        SI-unit input is implemented! Limits are checked! BA 2025-08-15

        Equation
        ----------
            Ce = a + b * S**n.

        Parameters
        ----------
        Comp_dict : TYPE, Dictionary.
            DESCRIPTION : This dictionary contains all the variables and paramters needed to
            find a cost estimate for a particular component. For the exact values in the dictionary
            check the excel file Capital_Investment_Methods or check the textbook corresponding to this
            method.
            Comp_dict_example= {
                "Category": "Compressor",
                "Component Name": "hydrogen compressor",
                "Component Attribute" : 1000
                }
        CI : TYPE, Float.
        DESCRIPTION : capital investment of investigated component
        S : TYPE,  Float.
        DESCRIPTION : capacity of investigated component
        n : TYPE, Float.
        DESCRIPTION : cost exponent (n < 1 - economy of scales)
        a,b : TYPE, Float.
        DESCRIPTION : constant values for known device costs (literature)
        verbose : Boolean, optional
            DESCRIPTION : Should values be printed along with an explanation?
        Desired_year : TYPE, Float, optional.
            DESCRIPTION : The default is None. Do you want the cost index to be taken relative to the current year or another previous years?
            If you want the cost index to be takes relative to a previuos year, input value to Desired_year.


        Raises
        ------
        ValueError.
            DESCRIPTION : Checks if the component name is available in the Towler method excel sheet.

        Returns
        -------
        TYPE, String.
            DESCRIPTION : The installed cost of the component, adjusted to present day to account
            for inflation. This cost estimate also accounts for operational pressure and material of construction.

        """

        self.Component_category = Comp_dict.get("Category")
        self.Component_name = Comp_dict.get("Component Name")
        self.S = Comp_dict.get("Component Attribute")

        # Finds row corresponding to component and checks if component is available in this method
        index = np.where(self.Towler_xl_data[:, 1] == self.Component_name)[0]

        if index.size == 0:
            raise ValueError(
                "Component name is not found in the Towler method")

        # Array index contains the row for the component
        # Finds values needed for the cost estimation for the component
        Component_row = self.Towler_xl_data[index[0]]
        if Component_row[self.Towler_unit_col_index] in ("kW", "KW", "kPa", "KPa"):
            self.S = self.S/1000  # SI units, BA
        elif Component_row[self.Towler_unit_col_index] in ("l/s", "L/s"):
            self.S = self.S * 1000  # SI units, BA
        #limits = self.get_values_by_name(self.Component_name)
        self.check_value_within_limits(self.Component_name, self.S)

        a = float(Component_row[2])
        b = float(Component_row[3])
        n = float(Component_row[4])
        yr = float(Component_row[6])
        iF = float(Component_row[7])
        fm = float(Component_row[8])
        fl = float(Component_row[9])
        cF = float(Component_row[10])

        # Calculates cost of compoennt
        CI = a + b * (np.abs(self.S)**n)
        CI = self._Find_Present_Cost(CI, yr, plot=verbose, Current_year=(
            Desired_year is None), Desired_year=Desired_year) * iF * fm * fl * cF

        if verbose == True:
            print(
                f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units). The price of the component using Towler Method : {CI} euro ")

        return float(CI)

    def get_values_by_name(self, name_value, columns=None, df=None):
        """
        Retrieve the values of specific columns for the row matching a given 'name' value.

        Parameters
        ----------
        name_value : str
            The value to search for in the 'name' column.
        columns : list of str, optional
            List of column names whose values should be returned.
            Defaults to ["S_lower", "S_upper"] if not provided.
        df : pandas.DataFrame, optional
            DataFrame in which to search. Defaults to self.Towler_df if not provided.

        Returns
        -------
        dict or None
            A dictionary mapping each requested column name to its value for the matching row,
            or None if no matching row is found.

        Notes
        -----
        - If multiple rows have the same 'name', only the first match is returned.
        - This method is flexible and can be used with any DataFrame and column list.
        """
        if df is None:
            df = self.Towler_df
        if columns is None:
            columns = ["S_lower", "S_upper"]

        row = df.loc[df["name"] == name_value]
        if row.empty:
            return None
        return {col: row.iloc[0][col] for col in columns}

    import warnings

    def check_value_within_limits(self, name_value, value,
                                  lower_col="S_lower", upper_col="S_upper",
                                  df=None, error=False):
        """
        Check if a given value lies within predefined limits from a DataFrame entry.

        Parameters
        ----------
        name_value : str
            The value to search for in the 'name' column of the DataFrame.
        value : float
            The numeric value to be checked.
        lower_col : str, optional
            Column name for the lower limit. Default is "S_lower".
        upper_col : str, optional
            Column name for the upper limit. Default is "S_upper".
        df : pandas.DataFrame, optional
            DataFrame to search in. Defaults to self.Towler_df.
        error : bool, optional
            If True, raises a ValueError when the value is out of range.
            If False, issues a UserWarning instead.

        Returns
        -------
        bool
            True if the value is within limits or if no limits are defined.
            False if the value is out of range.

        Notes
        -----
        - If the limits are missing or NaN, the check passes automatically.
        - If multiple rows match `name_value`, only the first is used.
        """
        self.warn = {'value': 0,
                     'message': 'All o.k.'}
        if df is None:
            df = self.Towler_df

        limits = self.get_values_by_name(
            name_value, columns=[lower_col, upper_col], df=df)

        if limits is None:
            return True  # No matching row → OK

        lower = limits.get(lower_col, None)
        upper = limits.get(upper_col, None)

        # If limits are missing or NaN → treat as OK
        if lower is None or upper is None or np.isnan(lower) or np.isnan(upper):
            return True

        if not (lower <= value <= upper):
            msg = (f"Value {value} is outside allowed range [{lower}, {upper}] "
                   f"for component '{name_value}'. The returned value is an extrapolation")
            self.warn = {'value': value/(lower + 1),
                         'message': msg}
            if error:
                raise ValueError(msg)
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("always")  # Oder "default"
                    warnings.warn(msg, UserWarning)
            return False

        return True

    def _Turton_Method(self, Comp_dict, verbose=False, Desired_year=None):
        """
        Cost estimation according to:

        Turton, R. (2003). Analysis, synthesis, and design of Chemical Processes. Prentice Hall.
        
        SI-unit input not implemented yet! Limits are not checked! BA 2025-08-15

        Parameters
        ----------
        Comp_dict : TYPE, Dictionary.
            DESCRIPTION. Contains input parameters which are used by the Turton method to calculate
            the cost of the  component. A sample of this dictionary would look like :
                Comp_dict = {
                "Category": "Pump",
                "Component Name": "Centrifugal Pump, Cast iron",
                "Component Attribute": 200,
                "Pressure": 1000             # For the turton method the pressures are in guage, 100 KPa = 1atm
                    }

        verbose : TYPE, Boolean, optional.
            should values be printed along with an explanation?
        Desired_year : TYPE, Float, optional
            Do you want the cost index to be taken relative to the current year or another previous years?

        Raises
        ------
        ValueError.
            DESCRIPTION : Checks if the component name is available in the Turton method excel sheet.

        Returns
        -------
        TYPE, String.
            DESCRIPTION : The cost of the component, adjusted to present day to account
            for inflation. This cost estimate also accounts for operational pressure and material of construction.

        """

        self.Component_category = Comp_dict.get("Component Catgeory")
        self.Component_name = Comp_dict.get("Component Name")
        self.S = Comp_dict.get("Component Attribute")
        self.Pressure = Comp_dict.get("Pressure")

        # Finds row corresponding to component and checks if component is available in this method
        index = np.where(self.Turton_xl_data[:, 1] == self.Component_name)[0]
        if index.size == 0:
            raise ValueError(
                "Component name is not found in the Turton method")

        # Array index contains the row for the component
        # Finds values needed for the cost estimation for the component
        Component_row = self.Turton_xl_data[index[0]]
        K1 = float(Component_row[2])
        K2 = float(Component_row[3])
        K3 = float(Component_row[4])
        B1 = float(Component_row[5])
        B2 = float(Component_row[6])
        n = float(Component_row[7])
        fm = float(Component_row[8])
        Fbm = float(Component_row[9])
        ccF = float(Component_row[10])
        cF2 = float(Component_row[18])
        yr = float(Component_row[19])
        fp = None
        c1 = None
        c2 = None
        c3 = None

        # Calculates the base cost of components, assuming ambient pressure and cs construction
        Cp_0 = K1 + K2 * np.log10(self.S) + K3 * (np.log10(self.S))**n
        Cp_0 = 10**Cp_0

        if any(x in self.Component_name for x in ["Compressor", "Turbine", "Liquid Expanders"]):

            CI = Cp_0 * Fbm * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif any(x in self.Component_name for x in ["Fixed Tube", "Floating Head", "U Tube"]):

            if self.Pressure <= 500:
                fp = 1
            elif 500 < self.Pressure <= 14000:
                c1 = -0.00164
                c2 = -0.00627
                c3 = -0.0123
                fp = c1 + c2 * np.log10(self.Pressure*cF2) + \
                    c3 * (np.log10(self.Pressure*cF2))**n
                fp = 10**fp
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")

            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif "Double Pipe" in self.Component_name:

            if self.Pressure <= 4000:
                fp = 1
            elif 4000 < self.Pressure <= 10000:
                c1 = 0.6072
                c2 = -0.9120
                c3 = 0.3327
                fp = c1 + c2 * np.log10(self.Pressure*cF2) + \
                    c3 * (np.log10(self.Pressure*cF2))**n
                fp = 10**fp
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")

            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif "Flat Plate" in self.Component_name:

            if self.Pressure < 1900:
                fp = 1
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")
            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif "Centrifugal Pump" in self.Component_name:

            if self.Pressure <= 1000:
                fp = 1
            elif 1000 < self.Pressure <= 10000:
                c1 = -0.3935
                c2 = -0.3957
                c3 = -0.00226
                fp = c1 + c2 * np.log10(self.Pressure*cF2) + \
                    c3 * (np.log10(self.Pressure*cF2))**n
                fp = 10**fp
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")

            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif any(x in self.Component_name for x in ["Positive Displacement Pump", "Reciprocating Pump"]):

            if self.Pressure <= 1000:
                fp = 1
            elif 1000 < self.Pressure <= 10000:
                c1 = -0.245382
                c2 = 0.259016
                c3 = -0.01363
                fp = c1 + c2 * np.log10(self.Pressure*cF2) + \
                    c3 * (np.log10(self.Pressure*cF2))**n
                fp = 10**fp
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")

            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)

        elif any(x in self.Component_name for x in ["Floating Roof", "Fixed Roof"]):

            if self.Pressure <= 7:
                fp = 1
            else:
                print(
                    "The operational pressure for the shell and tube heat exchanger is out of range for the Turton method")

            CI = Cp_0 * (B1 + (B2*fm*fp))
            CI = CI * ccF
            CI = self._Find_Present_Cost(CI, yr, plot=True, Current_year=(
                Desired_year is None), Desired_year=Desired_year)

            if verbose == True:
                print(
                    f"The name of this component is {self.Component_name}. The component attriute is {self.S} (units) and {self.Pressure} KPa. The price of the component using Turton Method : {CI} euro ")

            return float(CI)


"==========================================  TEST RUN.   =============================================="

if __name__ == "__main__":

    Eco = CAP_methods()

    Comp_dict = {
        "Category": "Compressor",
        "Component Name": "centrifugal compressor cs",
        "Component Attribute": 76000,  # SI units, Watt!

    }

    Cost_comp_couper_method = Eco.Towler_Method(
        Comp_dict, verbose=False, Desired_year=2024)
    print(f'Costs: {Cost_comp_couper_method:.3e}', Comp_dict, Eco.warn)
