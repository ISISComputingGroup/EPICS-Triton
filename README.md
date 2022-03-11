# EPICS-Triton
Support module for the Triton dilution fridge

Technically, "Triton" refers to the gas handling apparatus. This is what IBEX and SECI talk to. When setting up a triton, scientists may refer to it as a "Kelvinox". This is the technical name for the dilution insert, which is controlled by the triton gas handling apparatus.

To avoid confusion: all dilution fridges currently in use at ISIS are controlled by Triton gas handling systems, with one exception: the ICE fridge used on the muon beamlines.

## WIKI
Please see the WIKI for more information on Triton:
- https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Triton

## System Tests
The triton system tests are located in the [EPICS-IOC_Test_Frameork](https://github.com/ISISComputingGroup/EPICS-IOC_Test_Framework): `EPICS-IOC_Test_Framework\tests\triton.py`

To run the system tests, run the following command from and EPICS Terminal (`C:\Instrument\Apps\EPICS\config_env.bat`): `python run_tests.py -t triton`.

Use the `-a` flag if you want to run the triton emulator for manual testing.
