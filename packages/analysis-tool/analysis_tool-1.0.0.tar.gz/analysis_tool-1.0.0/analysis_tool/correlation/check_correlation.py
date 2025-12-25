'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-08-28 05:59:48 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-05-18 09:12:01 +0200
FilePath     : check_correlation.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import sys
import os
import argparse
import math
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Any

import multiprocessing

import numpy as np
from rich import print as rprint

from ROOT import gStyle, TGaxis
from ROOT import ROOT, RDataFrame, TChain, TTree, TFile, TObject, TTreeFormula, system, gROOT, gStyle, gRandom, TF1
from ROOT import kDashed, kRed, kGreen, kBlue, kBlack, kGray, kTRUE, kFALSE, gPad, TLegend
from ROOT import TMath, TAxis, TH1, TLatex, TROOT, TSystem, TCanvas, TFile, TTree, TObject, gROOT, TPaveText, TLegend
from ROOT import vector, TGraphAsymmErrors, TF1, TH2, TH1D, TH2D, TPad, TExec


from analysis_tool.utils.utils_ROOT import apply_cut_to_rdf, add_tmp_var_to_rdf, add_tmp_weight_to_rdf


@dataclass
class DalitzVariable:
    name: str
    expr: str
    title: str
    latex_name: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'DalitzVariable':
        return cls(
            name=data['name'],
            expr=data['expr'],
            title=data['title'],
            latex_name=data.get('latex_name', data['name']),
        )


def cal_correlation_factor(h2: TH2) -> float:
    """Calculate correlation factor from a 2D histogram.

    Args:
        h2: 2D histogram

    Returns:
        Correlation factor
    """
    correlation_factor = h2.GetCorrelationFactor()
    covariance = h2.GetCovariance()
    rprint(f'correlationFactor = {correlation_factor}')
    rprint(f'covariance        = {covariance}')
    return correlation_factor


def create_canvas_pads() -> Tuple[TCanvas, TPad, TPad, TPad]:
    """Create the canvas and pads for plotting.

    Returns:
        Tuple containing the canvas and three pads
    """
    c1 = TCanvas("c1", "c1", 1000, 900)
    gStyle.SetOptStat(0)

    center_pad = TPad("center_pad", "center_pad", 0.0, 0.0, 0.6, 0.6)
    center_pad.SetLeftMargin(0.15)
    center_pad.Draw()

    right_pad = TPad("right_pad", "right_pad", 0.55, 0.0, 1.0, 0.6)
    right_pad.Draw()

    top_pad = TPad("top_pad", "top_pad", 0.0, 0.55, 0.6, 1.0)
    top_pad.SetLeftMargin(0.15)
    top_pad.Draw()

    return c1, center_pad, right_pad, top_pad


def check_correlation(
    input_files: str,
    input_tree_name: str,
    varx: Union[dict[str, str], DalitzVariable],
    vary: Union[dict[str, str], DalitzVariable],
    selstring: Optional[str],
    weight_expr: str,
    output_plot_path: Union[str, Path],
    n_bins: int = 349,
    n_threads: int = 0,
) -> None:
    """Create a 2D correlation plot between two variables.

    Args:
        input_files: Path to ROOT input files, could be separated by comma
        input_tree_name: Name of the tree in ROOT files
        varx: Dictionary with 'name', 'expr', and 'title' for x-axis variable, or a DalitzVariable object
        vary: Dictionary with 'name', 'expr', and 'title' for x-axis variable, or a DalitzVariable object
        selstring: Selection string for filtering data
        weight_expr: Weight variable expression (or 'none'/'1' for no weights)
        output_plot_path: Path to save output plot
    """
    gROOT.SetBatch(1)
    if n_threads == 0:
        n_threads = max(1, multiprocessing.cpu_count() // 2 - 1)
    elif n_threads < 0:
        n_threads += max(multiprocessing.cpu_count(), 1)
    else:
        n_threads = max(n_threads, multiprocessing.cpu_count() - 1)
    ROOT.EnableImplicitMT(n_threads)

    # Read data into RDataFrame
    rdf = RDataFrame(input_tree_name, input_files.split(','))
    rdf = apply_cut_to_rdf(rdf, selstring)

    # Add temporary weight variable
    weight_name = '__weight_for_correlation'
    rdf, weight_name = add_tmp_weight_to_rdf(rdf, weight_expr, weight_name)

    # Convert dictionaries to dataclasses if needed
    varx = varx if isinstance(varx, DalitzVariable) else DalitzVariable.from_dict(varx)
    vary = vary if isinstance(vary, DalitzVariable) else DalitzVariable.from_dict(vary)

    # Add temporary variables to RDataFrame
    rdf, varx_name = add_tmp_var_to_rdf(rdf, varx.expr, varx.name)
    rdf, vary_name = add_tmp_var_to_rdf(rdf, vary.expr, vary.name)

    # Create 2D histogram
    h2 = rdf.Histo2D(
        ("h2", "", n_bins, rdf.Min(varx_name).GetValue(), rdf.Max(varx_name).GetValue(), n_bins, rdf.Min(vary_name).GetValue(), rdf.Max(vary_name).GetValue()), varx_name, vary_name, weight_name
    ).GetValue()

    # Calculate correlation factor
    correlation_factor: float = cal_correlation_factor(h2)

    # Create canvas and pads
    c1, center_pad, right_pad, top_pad = create_canvas_pads()

    # Create projections
    proj_h2_x = h2.ProjectionX()
    proj_h2_y = h2.ProjectionY()

    # Set axis titles
    h2.GetXaxis().SetTitle(varx.title)
    h2.GetYaxis().SetTitle(vary.title)

    # Draw 2D histogram
    center_pad.cd()
    gStyle.SetPalette(1)
    h2.Draw("COL")

    # Draw X projection
    top_pad.cd()
    proj_h2_x.SetFillColor(kBlue + 1)
    proj_h2_x.Draw("bar")

    # Draw Y projection
    right_pad.cd()
    proj_h2_y.SetFillColor(kBlue - 2)
    proj_h2_y.Draw("hbar")

    # Draw correlation text
    c1.cd()
    t = TLatex()
    t.SetTextFont(42)
    t.SetTextSize(0.025)
    t.DrawLatex(0.58, 0.88, "The correlation between")
    t.DrawLatex(0.58, 0.83, f"{varx.title} and {vary.title}")
    t.DrawLatex(0.58, 0.78, f"is {correlation_factor*100:.4f}%")

    # Optimize X projection
    xfirst = h2.GetXaxis().GetFirst()
    xlast = h2.GetXaxis().GetLast()
    xmin = h2.GetXaxis().GetBinLowEdge(xfirst)
    xmax = h2.GetXaxis().GetBinUpEdge(xlast)
    proj_h2_x.GetXaxis().SetRangeUser(xmin, xmax)
    proj_h2_x.SetMinimum(0)
    top_pad.Modified()

    # Optimize Y projection
    yfirst = h2.GetYaxis().GetFirst()
    ylast = h2.GetYaxis().GetLast()
    ymin = h2.GetYaxis().GetBinLowEdge(yfirst)
    ymax = h2.GetYaxis().GetBinUpEdge(ylast)
    proj_h2_y.GetXaxis().SetRangeUser(ymin, ymax)
    proj_h2_y.SetMinimum(0)
    right_pad.Modified()

    # Save output
    output_plot_path = Path(output_plot_path).resolve().as_posix()
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    c1.SaveAs(output_plot_path)

    return correlation_factor


def test_check_correlation():
    commonDir = '/home/uzh/wjie/workspace/output/Bs2JpsiKstar/fullAnalysis/output/v2r0/tuple/fullAna/Nominal/massfit/02fit/cutSysAnaNominal/Bs2JpsiKstar/15161718'

    # input_files = 'Bs2JpsiKstar/Bs2JpsiKstar_2018_selected.root'
    #    input_files = f'{commonDir}/Nominal/massfit/Bs2JpsiKstar/cutSysAnaNominal/02fit/15161718/data_Bs2JpsiKstar_15161718_preselected_reduced_sw2.root'

    input_files = f"{commonDir}/data_Bs2JpsiKstar_15161718_preselected_reduced_sw2.root"

    input_tree_name = 'DecayTree'
    varx = DalitzVariable(
        expr='cosh_PVFit_MassConsJpsi',
        name='cosh_PVFit_MassConsJpsi',
        title='cosh_PVFit_MassConsJpsi',
    )

    vary = DalitzVariable(
        expr='B_PVFit_MassConsJpsi_Mass',
        name='B_PVFit_MassConsJpsi_Mass',
        title='B_PVFit_MassConsJpsi_Mass',
    )

    selstring = '(B_PVFit_MassConsJpsi_Mass>5279.8-30) && (B_PVFit_MassConsJpsi_Mass<5279.8+30)'
    #    selstring = '(B_PVFit_MassConsJpsi_Mass>5250 && B_PVFit_MassConsJpsi_Mass<5310)'  # '(Kst_PVFit_MassConsJpsi_Mass > 931 && Kst_PVFit_MassConsJpsi_Mass < 966) && (B_PVFit_MassConsJpsi_Mass>5250 && B_PVFit_MassConsJpsi_Mass<5310)'
    weight_name = 'none'
    plot_dir = './output/correlation'
    #
    #    for _varx in ['cosh_PVFit_MassConsJpsi', 'cosl_PVFit_MassConsJpsi', 'phih_PVFit_MassConsJpsi']:
    #        check_correlation(input_files, input_tree_name, _varx, vary, selstring, weight_name, plot_dir)

    # varx = 'B_LOKI_DTF_CHI2NDOF'

    # vary = 'B_PVFit_MassConsJpsi_chi2_0/B_PVFit_MassConsJpsi_nDOF_0'

    for varx in ['cosh_PVFit_MassConsJpsi', 'cosl_PVFit_MassConsJpsi', 'phih_PVFit_MassConsJpsi']:

        _varx = DalitzVariable(
            expr=varx,
            name=varx,
            title=varx,
        )

        output_plot_path = f'{plot_dir}/{_varx.name}-{vary.name}.pdf'

        check_correlation(
            input_files,
            input_tree_name,
            _varx,
            vary,
            selstring,
            weight_name,
            output_plot_path,
        )


if __name__ == '__main__':
    test_check_correlation()
