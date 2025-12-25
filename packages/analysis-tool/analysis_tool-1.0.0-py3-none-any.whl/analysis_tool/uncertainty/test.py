'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-04-07 09:45:54 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-07 09:46:49 +0200
FilePath     : test.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

from analysis_tool.uncertainty.uncertainty_tools import ValErrPropagator, weighted_average

from rich import print as rprint

from uncertainties import ufloat


if __name__ == "__main__":
    val1_conf = {
        "value": 1,
        "stat": 0.1,
        "syst": 0.2,
        "syst1": 0.3,
    }
    val1 = ValErrPropagator(val1_conf, name="val1")

    val2 = 2

    val4_conf = {
        "value": 4,
        "stat": 0.4,
        "syst": 0.5,
        "syst2": 0.6,
    }
    val4 = ValErrPropagator(val4_conf, name="val4")

    rprint("\n\n\nExample of ValErrPropagator + ValErrPropagator")
    new_val = val1 + val4
    new_val.name = "new_val"
    rprint(new_val)
    new_val.print_result()

    # exit(1)
    rprint("\n val1 after the operation")
    rprint(val1)
    val1.print_result()

    rprint("\n val4 after the operation")
    rprint(val4)
    val4.print_result()

    # 2) weighted_average
    measurements = [
        ufloat(1.1, 0.1),
        ufloat(1.2, 0.2),
        ufloat(0.9, 0.3),
    ]

    combined_measurement = weighted_average(measurements)
    rprint("\n\n\nExample of weighted_average")
    rprint(f"Measurements: {measurements}")
    rprint(f"Combined measurement: {combined_measurement}")
