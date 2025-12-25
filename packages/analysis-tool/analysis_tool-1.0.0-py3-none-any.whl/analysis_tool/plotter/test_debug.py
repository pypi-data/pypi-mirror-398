'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-01-08 08:49:55 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-01-09 05:54:15 +0100
FilePath     : test_debug.py
Description  : 

Copyright (c) 2025 by everyone, All Rights Reserved. 
'''

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
from copy import deepcopy

from uncertainties import ufloat, unumpy
from dataclasses import dataclass, field
from typing import List
from rich import print as rprint

from compare_data_with_errorbar import compare_data_with_errorbar


if __name__ == '__main__':
    # Test the function
    x_labels = ['A', 'B', 'C']
    stat_ufloats_lists = [
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]),
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]) - 0.1,
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]) + 0.2,
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]) + 0.2,
    ]
    syst_ufloats_lists = None
    labels = ['Baseline', 'PT_1', 'PT_2', 'PT_3']
    xlabel = 'X Label'
    ylabel = 'Y Label'
    title = 'Title'
    # option = 'shiftToBaseline'  # [compareRawValues, shiftToBaseline, shiftToBaseline_and_projectToSigmaPlane]
    draw_axhline = None
    draw_grid = True

    # for option in ['compareRawValues', 'shiftToBaseline', 'shiftToBaseline_and_projectToSigmaPlane']:
    for option in ['shiftToBaseline']:
        output_file = f'output/test_{option}.png'

        # compare_data_with_errorbar
        compare_data_with_errorbar(
            x_labels=x_labels,
            stat_ufloats_lists=stat_ufloats_lists,
            syst_ufloats_lists=syst_ufloats_lists,
            labels=labels,
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            option=option,
            draw_axhline=draw_axhline,
            draw_grid=draw_grid,
            output_file=output_file,
            show_chi2=True,
            chi2_mode='baseline',
        )
