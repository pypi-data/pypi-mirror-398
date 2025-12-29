========
carbatpy
========


.. image:: https://img.shields.io/pypi/v/carbatpy.svg
        :target: https://pypi.python.org/pypi/carbatpy


.. image:: https://readthedocs.org/projects/carbatpy-010/badge/?version=latest
        :target: https://carbatpy-010.readthedocs.io/en/latest/
        :alt: Documentation Status



Modeling Carnot Batteries (Thermal Energy Storage), a Python package.
 

This is a project aiming to model thermal energy storages using heat pumps for 
charging, organic Rankine cycles (ORC) for discharging and different kinds of 
storages.
For this, it is planned to use detailed fluid models (as implemented e.g. in 
REFPROP, CoolProp, or TREND ) and setting up systems which can either be steady 
state or (later) also unsteady. For the moment a **Refprop** license is needed.
Since this project just starts, do not expect too much.

If **Trend** is installed and shall be used,
in the configuration file carbatpy.cb_config.py the dictionary _TREND has to be set from
{"USE_TREND":False, "TREND_DLL":"", 'TREND_PATH':""} to True and the two paths 
must be set as system variables. (The Trend part is only ready for thermodynamic 
data, no transport data!)


It is aimed to have heat exchangers, machines and storages as compounds, which 
can be combined to different charging and dicharging configurations. For these, 
the energy balance, mass balance and further relations will be applied/solved.
Later on also thermo-economic calculations are planned.

For the beginning, the solution of the spatially resolved heat exchanger 
profiles, a  boundary value problem, and its irreversibility will be 
implemented. An optimization will follow. 


Burak Atakan, University of Duisburg-Essen, Germany

You can contact us at: batakan [a t ]uni-duisburg.de or atakan.thermodynamik.duisburg [ a t] gmail.com



* Free software: MIT license
* Documentation: https://carbatpy-010.readthedocs.io/en/latest/


Features
--------
* Can actually calculate steady state heat pumps, ORCs and Carnot-batteries
    with two storage tank pairs. 
* Only thermodynamics (at the moment): no heat exchanger calculations, only
    minimum approach temperatures used.
* Fluid properties from Refprop (NIST)
* Fluid properties from TREND (RU Bochum, Prof. Roland Span) for thermodynamic
    property calculations.


* TODO
    * Include heat exchanger calculations (solvving the ODE with local properties)
    * Optimizing pressure levels for high second law efficiencies.
    * Reading the cycle configuration(s) and parameters from a file.
    

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
