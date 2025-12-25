'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 14:21:50 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-12-08 08:32:32 +0100
FilePath     : compare_distributions_classicalWay.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

import os
import argparse
import yaml
import uproot as ur
import numpy as np
import pandas
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import rcParams, style
import seaborn as sns


matplotlib.use('Agg')
# style.use('seaborn-muted')
# style.use('seaborn-ticks')
sns.set_style("ticks")  # Choose from 'darkgrid', 'whitegrid', 'dark', 'white', 'ticks'
rcParams.update({'font.size': 12})
rcParams['figure.figsize'] = 16, 8
rcParams['xtick.labelsize'] = 16
rcParams['ytick.labelsize'] = 16

hist_settings = {
    # 'bins': 149,
    'bins': 49,
    'density': True,
    'alpha': 0.3,
    'histtype': 'step',
    'lw': 2,
}

hist_colors = {0: 'black', 1: 'red', 2: 'blue', 3: 'green', 4: 'cyan', 5: 'magenta', 6: 'yellow', 7: 'white'}


def draw_errorbar(data, weight, color, hist_settings):
    '''
    draw poisson error
    data [numpy]
    weight [numpy]
    '''
    limits = [data.min(), data.max()]
    sum_weights = weight.sum()
    normalisation = hist_settings['bins'] / (sum_weights * (limits[1] - limits[0])) if hist_settings['density'] else 1

    # let numpy calculate the histogram entries
    histo, bin_edges = np.histogram(a=data, bins=hist_settings['bins'], range=limits, weights=weight)

    # calculate the middles of eachs bin, as this is where we want to plot the
    # errorbars
    bin_middles = 0.5 * (bin_edges[1:] + bin_edges[:-1])

    # we take the poisson error as estimated standard deviation, taking the
    # normalisation into account
    y_err = np.sqrt(histo) * normalisation

    plt.errorbar(bin_middles, histo * normalisation, yerr=y_err, color=color, fmt=',', alpha=hist_settings['alpha'])


def draw_hist_with_error(data, weight, label, color, hist_settings):
    # hist
    plt.hist(data, weights=weight, label=label, color=color, **hist_settings)
    # error
    draw_errorbar(data, weight, color, hist_settings)


def read_variables_from_yaml(mode, variables_files):
    variables = []
    for file in variables_files:
        with open(file, 'r') as stream:
            variables += list(yaml.safe_load(stream)[mode].keys())
    return variables


def draw_distributions(dataset, compare_vars, mode, plot_dir):
    '''
    datasets: [list(1D)]
        for example: ./myroot,DecayTree,none,MC).
        Args order: path_to_file, tree_name, weight_name(=none if N/A), label_name
    '''

    # -----------branches for comparison--------------#
    variables_files = compare_vars.split(',')
    compare_vars = read_variables_from_yaml(mode, variables_files) if '.yaml' in compare_vars else variables_files
    print('VARS:', compare_vars)

    # -----------read in files--------------#
    # datasets: [list(2D)]: datasets[*][0]=path_to_file, datasets[*][1]=tree_name, datasets[*][2]=weight_name, datasets[*][3]=label_name
    datasets = [ds.split(',') for ds in dataset]

    for dset in datasets:
        # dest[*][4]=drawVar_array
        dset.append(pandas.DataFrame(ur.open(f"{dset[0]}:{dset[1]}").arrays(library="np", expressions=compare_vars)))
        # dest[*][5]=weightVar_array
        if dset[2] == 'none':
            dset.append(np.ones(len(dset[4])))
        else:
            dset.append(ur.open(f"{dset[0]}:{dset[1]}").arrays(library="np", expressions=[dset[2]]))

    # PLOT
    # -----------prepare directory--------------#
    os.makedirs(plot_dir, exist_ok=True)

    # -----------plot all in one canvas--------------#
    n = len(compare_vars)
    cols = 2
    rows = int(np.ceil(n / cols))

    plt.figure(figsize=(cols * 10, rows * 8))
    for i_var in range(len(compare_vars)):
        var = compare_vars[i_var]
        plt.subplot(rows, cols, i_var + 1)

        for dset in datasets:
            if dset[2] == 'none':
                draw_hist_with_error(dset[4][var], dset[5], dset[3], hist_colors[datasets.index(dset)], hist_settings)
            else:
                draw_hist_with_error(dset[4][var], dset[5][dset[2]], dset[3], hist_colors[datasets.index(dset)], hist_settings)
                print("var : ", var, " ", dset[2])

        plt.title(var, fontsize=20)
        plt.legend()
    # plt.savefig(plot_dir + var + '.pdf')
    plot_name = f'{plot_dir}/comparePlots_{mode}.pdf' if '.yaml' in compare_vars else f'{plot_dir}/comparePlots_{",".join(compare_vars)}.pdf'
    plt.savefig(plot_name)

    # -----------plot individual variabless--------------#
    for var in compare_vars:

        plt.figure(figsize=(10, 8))
        for dset in datasets:
            if dset[2] == 'none':
                draw_hist_with_error(dset[4][var], dset[5], dset[3], hist_colors[datasets.index(dset)], hist_settings)
            else:
                draw_hist_with_error(dset[4][var], dset[5][dset[2]], dset[3], hist_colors[datasets.index(dset)], hist_settings)
                print("var : ", var, " ", dset[2])

        plt.title(var, fontsize=20)
        plt.legend()
        # plt.tight_layout()
        # plt.grid()
        plt.savefig(f'{plot_dir}/comparePlot_{var}.pdf')


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dataset',
        # nargs='+',
        action='append',
        help='Dataset to be compared (the following args are cocantated by comma, for example: ./myroot,DecayTree,none,none,MC). Args order: path_to_file, tree_name, weight_name(=none if N/A), label_name',
    )
    parser.add_argument(
        '--compare-vars',
        help='List of variables to be compared; if dict is given, then take list of the dictionary values',
    )
    parser.add_argument('--mode', help='Name of the selection in yaml with variables')
    parser.add_argument('--plot-dir', help='Output path of pdfs')

    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    draw_distributions(**vars(args))


if __name__ == '__main__':
    main()
