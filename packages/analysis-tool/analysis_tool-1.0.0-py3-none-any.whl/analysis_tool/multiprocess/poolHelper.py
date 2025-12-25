'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 15:37:16 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-07-09 10:52:21 +0200
FilePath     : poolHelper.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import contextlib
import os, sys
import json, yaml
import re


import multiprocessing

import timeit
from copy import deepcopy
from itertools import product
from pathlib import Path


# ----- Threads part -----
def get_optimal_n_threads(n_threads: int) -> int:
    """
    Validate and adjust the number of threads for optimal CPU utilization.

    This function ensures the thread count is within reasonable bounds and provides
    sensible defaults for different use cases.

    Parameters
    ----------
    num_threads : int
        Requested number of threads
        - 0: Auto mode (use half of available CPUs)
        - Negative: Use (total_cpus + num_threads) threads
        - Positive: Use specified number (capped at available CPUs)

    Returns
    -------
    int
        Validated number of threads to use

    Examples
    --------
    >>> get_optimal_n_threads(0)      # Auto: use half CPUs
    >>> get_optimal_n_threads(-1)     # Use all but one CPU
    >>> get_optimal_n_threads(-n)      # Use n_max - n CPUs
    >>> get_optimal_n_threads(16)     # Use 16 threads (if available)
    """
    total_cpu_count = multiprocessing.cpu_count()

    if n_threads == 0:
        # Auto mode: use half of available CPUs but ensure at least 1
        adjusted_threads = max(total_cpu_count // 2 - 1, 1)
    elif n_threads < 0:
        # Negative values: leave some CPUs free (e.g., -1 = all but one CPU)
        adjusted_threads = max(total_cpu_count + n_threads, 1)
    else:
        # Positive values: use requested threads but cap at available CPUs
        adjusted_threads = max(min(n_threads, total_cpu_count), 1)

    print(f"Thread configuration: requested={n_threads}, available_cpus={total_cpu_count}, optimal={adjusted_threads}")
    return adjusted_threads


def available_cpu_count():
    """
    Return the number of available virtual or physical CPUs on this system.
    The number of available CPUs can be smaller than the total number of CPUs
    when the cpuset(7) mechanism is in use, as is the case on some cluster
    systems.

    Adapted from http://stackoverflow.com/a/1006301/715090
    """
    with contextlib.suppress(IOError):
        status = Path('/proc/self/status').read_text()
        if m := re.search(r'(?m)^Cpus_allowed:\s*(.*)$', status):
            res = bin(int(m[1].replace(',', ''), 16)).count('1')
            if res > 0:
                return min(res, multiprocessing.cpu_count())
    return multiprocessing.cpu_count()


def callFuncWithMTP(func, param_lists, nCpu=multiprocessing.cpu_count()):
    '''
    Multiprocessing wrapper
    Call function with multiprocessing
    '''
    start = timeit.default_timer()
    print(f'The maximum number of cores to be used is {nCpu}')

    # Call the multiprocessing method
    with multiprocessing.Pool(processes=nCpu) as pool:
        ReturnList = pool.starmap(func, param_lists)

        end = timeit.default_timer()
        print(f'elapsed time of multiprocessing: {end - start}')

        return ReturnList
