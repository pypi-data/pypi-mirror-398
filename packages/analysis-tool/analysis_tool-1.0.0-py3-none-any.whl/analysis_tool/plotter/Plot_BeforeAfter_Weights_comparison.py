'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 14:22:36 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-12-06 14:22:36 +0100
FilePath     : Plot_BeforeAfter_Weights_comparison.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

###################################################
#
# Script for weighting in the Bs2JPsiKstar analysis
#
###################################################

import math, sys, os, json
import argparse
from array import array
import yaml

from ROOT import kDashed, kRed, kGreen, kBlue, kBlack, kGray, kTRUE, kFALSE, gPad
from ROOT import ROOT, RDataFrame, TMath, TAxis, TH1, TLatex, TROOT, TSystem, TCanvas, TFile, TTree, TObject, gROOT
from ROOT import vector, gStyle, TH1D, TLegend, TF1, TGaxis

import numpy as np
import uproot as ur
from hep_ml import reweight
import itertools
import pandas
import argparse

from .Plotter import MakeWeightingPlot


gROOT.SetBatch(1)

print(sys.argv)


from ..utils.utils_general import print_args


def read_variables_from_yaml(mode, variables_files):
    variables = []
    for file in variables_files:
        with open(file, 'r') as stream:
            variables += list(yaml.safe_load(stream)[mode].keys())
    return variables


def draw_plots(
    Channel,
    VariablesFiles,
    Selections,
    WeightOriginal,
    WeightTarget,
    Ranges,
    Labels,
    WeightFilesOriginal,
    WeightTreesOriginal,
    WeightFilesTarget,
    WeightTreesTarget,
    WeightName,
    PlotIndividual,
    OutputDir,
):
    # -----------start functions--------------#
    # for legend
    LableDict = {}
    LableDict.update({'BdData': '#it{B^{0}} data'})
    LableDict.update({'BsData': '#it{B^{0}_{s}} data'})
    LableDict.update({'BdMC': '#it{B^{0}} sim.'})
    LableDict.update({'BsMC': '#it{B^{0}_{s}} sim.'})
    ModeOriginal = f'{Channel}MC'
    ModeTarget = f'{Channel}Data'

    if ModeOriginal not in LableDict.keys():
        LableDict.update({ModeOriginal: ModeOriginal})
    if ModeTarget not in LableDict.keys():
        LableDict.update({ModeTarget: ModeTarget})

    # -----------read in files--------------#
    WeightFilesOriginals = WeightFilesOriginal.split(',')
    odf = RDataFrame(WeightTreesOriginal, WeightFilesOriginals).Filter(Selections)
    odf = odf.Define('_one', '1')
    weightOriginal = '_one' if (WeightOriginal == '' or WeightOriginal == '1') else WeightOriginal

    WeightFilesTargets = WeightFilesTarget.split(',')
    tdf = RDataFrame(WeightTreesTarget, WeightFilesTargets).Filter(Selections)
    tdf = tdf.Define('_one', "1") if (WeightTarget == '' or WeightTarget == '1') else tdf
    weightTarget = '_one' if (WeightTarget == '' or WeightTarget == '1') else WeightTarget

    print('Specified input original files: ', WeightFilesOriginals)
    print('Specified input target   files: ', WeightFilesTargets)

    ##############################################
    # PLOTTING
    ##############################################
    # -----------branches for comparison--------------#
    variables_files = VariablesFiles.split(',')
    obranches = read_variables_from_yaml(ModeTarget, variables_files) if variables_files[0].endswith('.yaml') else variables_files

    # -----------preparation--------------#
    gROOT.ProcessLine(".x style/MylhcbStyle.C")
    gStyle.SetLabelSize(26, "xyz")
    gStyle.SetTitleSize(22, "y")
    gStyle.SetTitleSize(28, "x")

    NBINS = 70

    os.makedirs(OutputDir, exist_ok=True)

    rangesTmp = Ranges.replace('m', '-').split('+')
    ranges = []
    for r in rangesTmp:
        ranges.append([float(r.split(',')[0].replace('m', '-')), float(r.split(',')[1].replace('m', '-'))])

    lables = Labels.split(',')

    nVar = len(obranches)

    cc = TCanvas('cc', 'cc', 600 * nVar, 1000)
    if nVar > 5:
        gStyle.SetLineScalePS(0.5)
    else:
        gStyle.SetLineScalePS(1.8)
    # create a canvas with the correct pads
    cc.Divide(nVar, 4)
    for i in range(1, nVar + 1):
        cc.GetPad(i).SetPad(float(i - 1) / nVar, 0.7, float(i) / nVar, 1)
        cc.GetPad(i + nVar).SetPad(float(i - 1) / nVar, 0.5, float(i) / nVar, 0.7)
        cc.GetPad(i).SetTopMargin(0.1)
        cc.GetPad(i).SetBottomMargin(0)
        cc.GetPad(i).SetLeftMargin(0.15)
        cc.GetPad(i).SetRightMargin(0.15)
        cc.GetPad(i + nVar).SetBottomMargin(0.35)
        cc.GetPad(i + nVar).SetTopMargin(0)
        cc.GetPad(i + nVar).SetLeftMargin(0.15)
        cc.GetPad(i + nVar).SetRightMargin(0.15)
    for i in range(2 * nVar + 1, 2 * nVar + 1 + nVar):
        cc.GetPad(i).SetPad(float(i - 2 * nVar - 1) / nVar, 0.2, float(i - 2 * nVar) / nVar, 0.5)
        cc.GetPad(i + nVar).SetPad(float(i - 2 * nVar - 1) / nVar, 0, float(i - 2 * nVar) / nVar, 0.2)
        cc.GetPad(i).SetTopMargin(0.1)
        cc.GetPad(i).SetBottomMargin(0)
        cc.GetPad(i).SetLeftMargin(0.15)
        cc.GetPad(i).SetRightMargin(0.15)
        cc.GetPad(i + nVar).SetBottomMargin(0.35)
        cc.GetPad(i + nVar).SetTopMargin(0)
        cc.GetPad(i + nVar).SetLeftMargin(0.15)
        cc.GetPad(i + nVar).SetRightMargin(0.15)
    hoBef = []
    htBef = []
    hRatioBef = []
    hoAfter = []
    htAfter = []
    hRatioAfter = []
    RatioLines = []
    texts = []
    legs = []
    for i, var in enumerate(obranches):
        cc.cd(i + 1)
        print(var, NBINS, ranges[i][0], ranges[i][1], var, weightTarget)
        # exit(1)
        htBef.append(tdf.Histo1D(('target_before_' + var, 'target_before_' + var, NBINS, ranges[i][0], ranges[i][1]), var, weightTarget).GetValue())
        # htBef[-1].Sumw2()
        htBef[-1].Scale(1.0 / htBef[-1].Integral())
        htBef[-1].Draw()
        htBef[-1].GetXaxis().SetNoExponent()
        htBef[-1].SetMinimum(0.0001)
        htBef[-1].SetLineColor(2)
        htBef[-1].SetMarkerColor(2)
        htBef[-1].SetMarkerStyle(25)

        hoBef.append(odf.Histo1D(('original_before_' + var, 'original_before_' + var, NBINS, ranges[i][0], ranges[i][1]), var, weightOriginal).GetValue())
        # hoBef[-1].Sumw2()
        hoBef[-1].Scale(1.0 / hoBef[-1].Integral())
        hoBef[-1].Draw('same')
        htBef[-1].SetMaximum(max(htBef[-1].GetMaximum(), hoBef[-1].GetMaximum()) + 0.3 * (max(htBef[-1].GetMaximum(), hoBef[-1].GetMaximum()) - min(htBef[-1].GetMinimum(), hoBef[-1].GetMinimum())))
        legs.append(TLegend(0.35, 0.73, 0.85, 0.88))
        legs[-1].SetNColumns(2)
        legs[-1].SetTextFont(133)
        legs[-1].SetTextSize(26)
        legs[-1].SetFillStyle(0)
        legs[-1].SetBorderSize(0)

        print(LableDict[ModeOriginal])
        print(LableDict)
        legs[-1].AddEntry(hoBef[-1], LableDict[ModeOriginal], 'lp')
        legs[-1].AddEntry(htBef[-1], LableDict[ModeTarget], 'lp')
        legs[-1].Draw()

        # ratio plot
        cc.cd(i + nVar + 1)
        # hoBef[-1].Sumw2()
        # htBef[-1].Sumw2()
        hRatioBef.append(TH1D('Ratio_before_' + var, 'Ratio_before_' + var, NBINS, ranges[i][0], ranges[i][1]))
        hRatioBef[-1].Divide(htBef[-1], hoBef[-1])
        hRatioBef[-1].Draw()
        hRatioBef[-1].SetMaximum(2.8)
        hRatioBef[-1].SetMinimum(0)
        hRatioBef[-1].SetLineColor(2)
        hRatioBef[-1].SetMarkerColor(1)
        hRatioBef[-1].SetMarkerStyle(25)
        hRatioBef[-1].GetXaxis().SetTitle(lables[i])
        hRatioBef[-1].GetXaxis().SetTitleOffset(1.1)
        hRatioBef[-1].GetYaxis().SetTitle("#frac{N(" + LableDict[ModeTarget] + ")}{N(" + LableDict[ModeOriginal] + ")}")
        hRatioBef[-1].GetYaxis().SetTitleOffset(1.5)
        RatioLines.append(TF1("fbef" + var, "1", -100000, 1000000))
        RatioLines[-1].Draw("same")
        RatioLines[-1].SetLineStyle(1)
        RatioLines[-1].SetLineColor(1)

        cc.cd(i + 2 * nVar + 1)
        htAfter.append(tdf.Histo1D(('target_after_' + var, 'target_after_' + var, NBINS, ranges[i][0], ranges[i][1]), var, weightTarget).GetValue())
        htAfter[-1].Scale(1.0 / htAfter[-1].Integral())
        htAfter[-1].Draw()
        htAfter[-1].GetXaxis().SetNoExponent()
        htAfter[-1].SetMinimum(0.0001)
        htAfter[-1].SetLineColor(2)
        htAfter[-1].SetMarkerColor(2)
        htAfter[-1].SetMarkerStyle(25)
        hoAfter.append(odf.Histo1D(('o_after_' + var, 'o_after_' + var, NBINS, ranges[i][0], ranges[i][1]), var, WeightName).GetValue())
        hoAfter[-1].Scale(1.0 / hoAfter[-1].Integral())
        hoAfter[-1].Draw('same')
        htAfter[-1].SetMaximum(
            max(htAfter[-1].GetMaximum(), hoAfter[-1].GetMaximum()) + 0.3 * (max(htAfter[-1].GetMaximum(), hoAfter[-1].GetMaximum()) - min(htAfter[-1].GetMinimum(), hoAfter[-1].GetMinimum()))
        )
        # ratio plot
        cc.cd(i + 3 * nVar + 1)
        # hoAfter[-1].Sumw2()
        # htAfter[-1].Sumw2()
        hRatioAfter.append(TH1D('Ratio_after_' + var, 'Ratio_after_' + var, NBINS, ranges[i][0], ranges[i][1]))
        hRatioAfter[-1].Divide(htAfter[-1], hoAfter[-1])
        hRatioAfter[-1].Draw()
        hRatioAfter[-1].SetMaximum(2.8)
        hRatioAfter[-1].SetMinimum(0)
        hRatioAfter[-1].SetLineColor(2)
        hRatioAfter[-1].SetMarkerColor(1)
        hRatioAfter[-1].SetMarkerStyle(25)
        hRatioAfter[-1].GetXaxis().SetTitle(lables[i])
        hRatioAfter[-1].GetXaxis().SetTitleOffset(1.1)
        hRatioAfter[-1].GetYaxis().SetTitle("#frac{N(" + LableDict[ModeTarget] + ")}{N(" + LableDict[ModeOriginal] + ")}")
        hRatioAfter[-1].GetYaxis().SetTitleOffset(1.5)
        RatioLines.append(TF1("fafter" + var, "1", -100000, 1000000))
        RatioLines[-1].Draw("same")
        RatioLines[-1].SetLineStyle(1)
        RatioLines[-1].SetLineColor(1)

    cc.Print(f'{OutputDir}/WeightingPlots.pdf')
    cc.Draw()

    ##If asked for: Plot individual variables
    if PlotIndividual == "1":
        for i, var in enumerate(obranches):
            varN = var.replace(',', '-').replace('(', '').replace(')', '')
            MakeWeightingPlot(
                hoBef[i],
                htBef[i],
                hoAfter[i],
                htAfter[i],
                lables[i],
                ranges[i],
                NBINS,
                LableDict[ModeOriginal],
                LableDict[ModeTarget],
                "W. " + LableDict[ModeOriginal],
                LableDict[ModeTarget],
                f'{OutputDir}/WeightingPlots_Plot_{varN}.pdf',
                scale=0.9,
            )


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument("--Channel", type=str, default="Bd", choices=['Bs', 'Bd'], help="channel used")

    parser.add_argument('--VariablesFiles', type=str, action='store', default="", dest='VariablesFiles', help='variables to be weighted. e.g. (hminus_PT;hplus_PT;hminus_P;hplus_P)')

    parser.add_argument('--Selections', action='store', default="", dest='Selections')

    parser.add_argument('--WeightOriginal', type=str, action='store', default="", dest='WeightOriginal')
    parser.add_argument('--WeightTarget', type=str, action='store', default="", dest='WeightTarget')

    parser.add_argument('--WeightFilesOriginal', action='store', default="", dest='WeightFilesOriginal')
    parser.add_argument('--WeightTreesOriginal', action='store', default="", dest='WeightTreesOriginal')
    parser.add_argument('--WeightFilesTarget', action='store', default="", dest='WeightFilesTarget')
    parser.add_argument('--WeightTreesTarget', action='store', default="", dest='WeightTreesTarget')

    parser.add_argument('--WeightName', action='store', default="", dest='WeightName')

    parser.add_argument('--OutputDir', action='store', default="./tmp", dest='OutputDir')

    parser.add_argument('--Ranges', action='store', default="", dest='Ranges', help='990,1050+0,500000+0,40000')
    parser.add_argument('--Labels', type=str, action='store', default="", dest='Labels')
    parser.add_argument('--PlotIndividual', action='store', default="1", dest='PlotIndividual')


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    draw_plots(**vars(args))


if __name__ == '__main__':
    main()
