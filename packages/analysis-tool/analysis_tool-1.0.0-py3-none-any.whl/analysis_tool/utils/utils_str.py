'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 15:31:48 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-09-19 03:43:21 +0200
FilePath     : utils_str.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

import contextlib
import os, sys
import random
import json, yaml
import re
import inspect
import textwrap
from itertools import chain
from collections.abc import Mapping
import multiprocessing
import string
import shlex
import argparse
import timeit
from copy import deepcopy
from itertools import product
from pathlib import Path

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import colorsys

import colorama


# ----- String part -----
def splitpath(path: str):
    """Common helper
    Split path to certain file into 5 parts.
        path: [str] the input path
    Return a dictionary.
    {'path': _, 'folderPath': _, 'filename': _, 'rawfilename': _, 'extendName': _,}
        path: [str] the input path.
        folderPath: [str] the folder to path.
        filename: [str] file name with extension suffix.
        rawfilename: [str] file name without extension suffix.
        extendname: [str] extension suffix.
    """
    folderPath, filename = os.path.split(path)
    rawfilename, extendName = os.path.splitext(filename)
    return {
        'path': path,
        'folderPath': folderPath,
        'filename': filename,
        'rawfilename': rawfilename,
        'extendname': extendName,
    }


def wrap_quotationMark(argExpr: str):
    """wrap quotation mark to argExpr if it is not wrapped

    Args:
        argExpr (str): input expression

    Returns:
        str: the expression with quotation mark
    """

    if (not argExpr.startswith('"')) and (not argExpr.endswith('"')):
        return f'"{argExpr}"'
    else:
        return argExpr


def remove_quotationMark(argExpr: str):
    """remove quotation mark to argExpr if it is wrapped

    Args:
        argExpr (str): input expression

    Returns:
        str: the expression without quotation mark
    """
    if argExpr.startswith('"') and argExpr.endswith('"'):
        return argExpr[1:-1]
    else:
        return argExpr


def combine_cuts(cuts: list):
    # remove duplicated parentheses
    def _remove_duplicated_outer_parentheses(cut: str):
        if cut.startswith('((') and cut.endswith('))'):
            cut = cut[1:-1]
            return _remove_duplicated_outer_parentheses(cut)
        else:
            return cut

    # check input format
    cuts = cuts if isinstance(cuts, list) else [cuts]

    # combine cuts
    combined_cut = ''
    for cut in cuts:
        cut = _remove_duplicated_outer_parentheses(cut)
        # combined_cut = _remove_duplicated_outer_parentheses(combined_cut)
        # combined_cut = cut if combined_cut == '' else f'({combined_cut}) && ({cut})'
        combined_cut = cut if combined_cut == '' else f'({cut}) && ({combined_cut})'

    # remove those duplicated cut expression in combined_cut
    for cut in cuts:
        if combined_cut.count(f'({cut})') > 1:
            combined_cut = combined_cut.replace(f'({cut}) && ', '', 1)

    return f'({combined_cut})'


def split_expr(expr, nCol, s):
    '''
    Split expression which concatenated by specific symbol into a list,
    each element contains at most certain specific symbol
        expr: [str] expression to be splitted
        nCol: [int] the maximum of specific symbol contained in each element
        s: [*] the symbol required to split expression
    '''
    vars_list = []

    while expr.count(s) > nCol:
        expr = expr.split(s, nCol)
        vars_list.append(s.join(expr[:nCol]))
        expr = expr[nCol]

    vars_list.append(expr)

    return vars_list
