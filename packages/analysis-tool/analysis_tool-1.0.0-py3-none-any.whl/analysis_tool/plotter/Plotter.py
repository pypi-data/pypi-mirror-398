'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-02-16 13:17:13 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-12-06 14:21:12 +0100
FilePath     : Plotter.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

import sys, os
import argparse
import math
import numpy
from pathlib import Path

from ROOT import gStyle, TGaxis
from ROOT import ROOT, RDataFrame, TChain, TTree, TFile, TObject, TTreeFormula, system, gROOT, gStyle, TH1D, TLegend, TF1, TCanvas
from ROOT import kDashed, kRed, kGreen, kBlue, kBlack, kGray, kTRUE, kFALSE, gPad, TLegend
from ROOT import TMath, TAxis, TH1, TLatex, TROOT, TSystem, TCanvas, TFile, TTree, TObject, gROOT, TPaveText
from ROOT import vector, TGraphAsymmErrors, TF1, TH1D

import yaml


def read_variables_and_expressions_from_yaml(mode, variables_files):  # -> list, list:
    variables = []
    expressions = []
    for file in variables_files:
        with open(file, 'r') as stream:
            read_dict = yaml.safe_load(stream)[mode]
            variables += list(read_dict.keys())
            expressions += list(read_dict.values())

    return variables, expressions


def helper_set_histStyle_ht(hist, style=0):
    '''
    style: [int] 0: point like, 1: curve like
    '''
    hist.GetXaxis().SetNoExponent()
    hist.SetMinimum(0.0001)
    if style == 0:
        hist.SetLineColor(2)
        hist.SetMarkerColor(2)
        hist.SetMarkerStyle(25)
    else:
        hist.SetLineColor(kBlack)
        hist.SetFillColor(kGray + 2)
        hist.SetFillStyle(1001)


def helper_set_histStyle_ho(hist, style=0):
    '''
    style: [int] 0: point like, 1: curve like
    '''
    hist.GetXaxis().SetNoExponent()
    hist.SetMinimum(0.0001)
    if style == 0:
        hist.SetLineColor(1)
        hist.SetMarkerColor(1)
        hist.SetMarkerStyle(15)
    else:
        hist.SetLineColor(kRed)
        hist.SetFillColor(kRed - 4)
        # hist.SetFillStyle(3644)
        hist.SetFillStyle(3013)


def helper_set_hRatio(hRatio, xTitle, yTitle):
    hRatio.SetMaximum(2.8)
    hRatio.SetMinimum(0)
    hRatio.SetLineColor(2)
    hRatio.SetMarkerColor(1)
    hRatio.SetMarkerStyle(25)

    hRatio.GetXaxis().SetTitle(xTitle)
    hRatio.GetXaxis().SetTitleOffset(1.1)

    hRatio.GetYaxis().SetTitle(yTitle)
    hRatio.GetYaxis().SetTitleOffset(1.5)


def get_RatioLines(name, ranges: tuple):  # -> TF1:
    RatioLines = TF1(name, "1", ranges[0], ranges[1])
    RatioLines.SetLineStyle(1)
    RatioLines.SetLineColor(1)
    return RatioLines


# -----------draw plots for comparison before and after weight individually--------------#
def MakeWeightingPlot(hoBef, htBef, hoAfter, htAfter, xTitle, Range, NBINS, oName, tName, oNameW, tNameW, output, scale=1):
    gStyle.SetLineScalePS(2.4 * scale)
    gStyle.SetLabelSize(int(28 * scale), "xyz")
    gStyle.SetTitleSize(int(24 * scale), "y")
    gStyle.SetTitleSize(int(32 * scale), "x")
    gStyle.SetTitleSize(int(32 * scale), "x")

    TGaxis.SetMaxDigits(5)

    hoBef.UseCurrentStyle()
    htBef.UseCurrentStyle()

    if hoAfter and htAfter:
        # comparison after reweighting
        hoAfter.UseCurrentStyle()
        htAfter.UseCurrentStyle()
        c = TCanvas('c', 'c', 500, 800)
        c.Divide(1, 4)
    else:
        c = TCanvas('c', 'c', 500, 400)
        c.Divide(1, 2)

    def helper_setPad_DistributionAndRatio(pad_Distribution, pad_Ratio):
        # pad for distribution
        pad_Distribution.SetTopMargin(0.05)
        pad_Distribution.SetBottomMargin(0)
        pad_Distribution.SetLeftMargin(0.2)
        pad_Distribution.SetRightMargin(0.12)
        # pad for ratio
        pad_Ratio.SetBottomMargin(0.48)
        pad_Ratio.SetTopMargin(0)
        pad_Ratio.SetLeftMargin(0.2)
        pad_Ratio.SetRightMargin(0.12)

    if hoAfter and htAfter:
        # compare both before and after reweighting
        c.GetPad(1).SetPad(0, 0.73, 1, 1)
        c.GetPad(2).SetPad(0, 0.5, 1, 0.73)
        helper_setPad_DistributionAndRatio(c.GetPad(1), c.GetPad(2))

        c.GetPad(3).SetPad(0, 0.23, 1, 0.5)
        c.GetPad(4).SetPad(0, 0, 1, 0.23)
        helper_setPad_DistributionAndRatio(c.GetPad(3), c.GetPad(4))
    else:
        # compare before reweighting only
        c.GetPad(1).SetPad(0, 0.73 / 2, 1, 1)
        c.GetPad(2).SetPad(0, 0, 1, 0.73 / 2)
        helper_setPad_DistributionAndRatio(c.GetPad(1), c.GetPad(2))

    RatioLines = []
    texts = []
    legs = []
    c.cd(1)
    htBef.Sumw2()
    htBef.Scale(1.0 / htBef.Integral())
    htBef.GetXaxis().SetNoExponent()

    hoBef.Sumw2()
    hoBef.Scale(1.0 / hoBef.Integral())

    helper_set_histStyle_ht(htBef, 1)
    helper_set_histStyle_ho(hoBef, 1)

    htBef.Draw('hist')
    hoBef.Draw('histsame')

    htBef.SetMinimum(0.0001)
    htBef.SetMaximum(max(htBef.GetMaximum(), hoBef.GetMaximum()) + 0.4 * (max(htBef.GetMaximum(), hoBef.GetMaximum()) - min(htBef.GetMinimum(), hoBef.GetMinimum())))

    legs.append(TLegend(0.23, 0.74, 0.85, 0.89))
    legs[-1].SetNColumns(2)
    legs[-1].SetTextFont(133)
    legs[-1].SetTextSize(int(30 * scale))
    legs[-1].SetFillStyle(0)
    legs[-1].SetBorderSize(0)
    legs[-1].AddEntry(hoBef, oName, 'F')
    legs[-1].AddEntry(htBef, tName, 'F')
    legs[-1].Draw()

    # ratio plot
    c.cd(2)
    hoBef.Sumw2()
    htBef.Sumw2()
    hRatioBef = TH1D(hoBef)
    hRatioBef.SetName('ratio_before')
    hRatioBef.Divide(htBef, hoBef)
    hRatioBef.Draw()

    helper_set_hRatio(hRatioBef, xTitle, "#frac{N(" + tName + ")}{N(" + oName + ")}")

    # Get the left and right range of the ratio plot
    RatioLines.append(get_RatioLines("fbef", (hRatioBef.GetXaxis().GetXmin(), hRatioBef.GetXaxis().GetXmax())))
    RatioLines[-1].Draw("same")

    if hoAfter and htAfter:
        c.cd(3)
        htAfter.Scale(1.0 / htAfter.Integral())
        htAfter.GetXaxis().SetNoExponent()
        hoAfter.Scale(1.0 / hoAfter.Integral())

        helper_set_histStyle_ht(htAfter, 1)
        helper_set_histStyle_ho(hoAfter, 1)

        htAfter.Draw('hist')
        hoAfter.Draw('histsame')

        htAfter.SetMinimum(0.0001)
        htAfter.SetMaximum(max(htAfter.GetMaximum(), hoAfter.GetMaximum()) + 0.4 * (max(htAfter.GetMaximum(), hoAfter.GetMaximum()) - min(htAfter.GetMinimum(), hoAfter.GetMinimum())))

        legs.append(TLegend(0.23, 0.74, 0.85, 0.89))
        legs[-1].SetNColumns(2)
        legs[-1].SetTextFont(133)
        legs[-1].SetTextSize(int(30 * scale))
        legs[-1].SetFillStyle(0)
        legs[-1].SetBorderSize(0)
        legs[-1].AddEntry(hoAfter, oNameW, 'F')
        legs[-1].AddEntry(htAfter, tNameW, 'F')
        legs[-1].Draw()

        # ratio plot
        c.cd(4)
        hoAfter.Sumw2()
        htAfter.Sumw2()
        hRatioAfter = TH1D(hoAfter)
        hRatioAfter.SetName('ratio_after')
        hRatioAfter.Divide(htAfter, hoAfter)
        hRatioAfter.Draw()

        helper_set_hRatio(hRatioAfter, xTitle, "#frac{N(" + tName + ")}{N(" + oName + ")}")
        RatioLines.append(get_RatioLines("fafter", (hRatioAfter.GetXaxis().GetXmin(), hRatioAfter.GetXaxis().GetXmax())))
        RatioLines[-1].Draw("same")

    output = str(Path(output).resolve())
    c.SaveAs(output)
    print(f"Create plot {output}")


# -----------draw plots for comparison before and after weight all in one canvas--------------#
def MakeWeightingPlot_all(
    VariablesFiles,
    mode,
    Selections,
    WeightOriginal,
    WeightTarget,
    Ranges,
    ModeOriginal,
    ModeTarget,
    XTitles,
    WeightFilesOriginal,
    WeightTreesOriginal,
    WeightFilesTarget,
    WeightTreesTarget,
    AllWeightName,  # All weights which apply to original file to show the power of reweighting
    PlotIndividual,
    OutputDir,
):
    gROOT.SetBatch(1)

    # ---------------general type checking--------------#
    Selections = Selections or '(1>0)'

    # -----------start functions--------------#
    # for legend
    LableDict = {}
    LableDict['BdData'] = '#it{B^{0}} data'
    LableDict['BsData'] = '#it{B^{0}_{s}} data'
    LableDict['BdMC'] = '#it{B^{0}} sim.'
    LableDict['BsMC'] = '#it{B^{0}_{s}} sim.'

    if ModeOriginal not in LableDict.keys():
        LableDict[ModeOriginal] = ModeOriginal
    if ModeTarget not in LableDict.keys():
        LableDict[ModeTarget] = ModeTarget

    # -----------read in files--------------#
    WeightFilesOriginals = WeightFilesOriginal.split(',')
    odf = RDataFrame(WeightTreesOriginal, WeightFilesOriginals).Filter(Selections)
    odf = odf.Define('weightOriginal', '1') if WeightOriginal == 'none' else odf.Define('weightOriginal', f'{WeightOriginal}')
    odf = odf.Define('allWeightName', f'{AllWeightName}') if AllWeightName else odf
    # odf = odf.Define('weightOriginal', f'{WeightOriginal}')
    # weightOriginal = check_weight_name_format(WeightOriginal)

    WeightFilesTargets = WeightFilesTarget.split(',')
    tdf = RDataFrame(WeightTreesTarget, WeightFilesTargets).Filter(Selections)
    tdf = tdf.Define('weightTarget', '1') if WeightTarget == 'none' else tdf.Define('weightTarget', f'{WeightTarget}')

    # tdf = tdf.Define('_one', '1')
    # weightTarget = check_weight_name_format(WeightTarget)

    print('Specified input original files: ', WeightFilesOriginals)
    print('Specified input target   files: ', WeightFilesTargets)

    ##############################################
    # PLOTTING
    ##############################################
    # -----------branches for comparison--------------#
    variables_files = VariablesFiles.split(',')
    obranches, oexpressions = read_variables_and_expressions_from_yaml(mode, variables_files) if variables_files[0].endswith('.yaml') else (variables_files, variables_files)
    nVar = len(obranches)

    # -----------Check all branches are available--------------#
    o_cols = odf.GetColumnNames()
    t_cols = tdf.GetColumnNames()
    for var, expr in zip(obranches, oexpressions):
        if var == expr:
            assert var in o_cols, f"Branch {var} not found in original file"
            assert var in t_cols, f"Branch {var} not found in target file"
        else:
            if var not in o_cols:
                print(f"Branch {var} not found in original file, try to define it from expression {expr}")
                odf = odf.Define(var, expr)
            if var not in t_cols:
                print(f"Branch {var} not found in target file, try to define it from expression {expr}")
                tdf = tdf.Define(var, expr)

    # set numpy columns for range usage
    ocols = odf.AsNumpy(obranches)
    tcols = tdf.AsNumpy(obranches)

    # -----------preparation--------------#
    OutputDir = str(Path(OutputDir).resolve())
    Path(OutputDir).mkdir(parents=True, exist_ok=True)

    # gROOT.ProcessLine(".x style/MylhcbStyle.C")
    gROOT.ProcessLine(f'.x {os.environ["PYTHONPATH_ANA_ANGULAR"]}/style/MylhcbStyle.C')

    gStyle.SetLabelSize(26, "xyz")
    gStyle.SetTitleSize(22, "y")
    gStyle.SetTitleSize(28, "x")

    NBINS = 70

    # -----------set drawing range--------------#
    ranges = []
    if 'auto' in Ranges:
        # just use pre-defined ranges as within percentage of [0.1%, 99.9%] sorted for certain variable
        # or, use customized ranges as within certain percentage e.g.: auto+0.01,99.9 sorted for certain variable
        rangesTmp = Ranges.removeprefix('auto+').removesuffix('+auto').replace('m', '-')
        percentRange = [0.1, 99.9] if Ranges == 'auto' else [float(rangesTmp.split(',')[0]), float(rangesTmp.split(',')[1])]

        for var in obranches:
            ranges.append(
                [
                    numpy.minimum(numpy.percentile(ocols[var], percentRange), numpy.percentile(tcols[var], percentRange))[0],
                    numpy.maximum(numpy.percentile(ocols[var], percentRange), numpy.percentile(tcols[var], percentRange))[1],
                ]
            )
    else:
        # use fully customized ranges, defined for each variable considered and separated by '+'
        rangesTmp = Ranges.replace('m', '-').split('+')
        for r in rangesTmp:
            ranges.append([float(r.split(',')[0].replace('m', '-')), float(r.split(',')[1].replace('m', '-'))])

    # -----------general pre-definition--------------#
    # xTitles = XTitles.split(',')

    xTitles = XTitles.split(',') if XTitles else obranches
    gStyle.SetLineScalePS(0.5) if nVar > 5 else gStyle.SetLineScalePS(1.8)

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
        print(var, NBINS, ranges[i][0], ranges[i][1], var, WeightTarget)
        htBef.append(tdf.Histo1D((f'target_before_{var}', f'target_before_{var}', NBINS, ranges[i][0], ranges[i][1]), var, 'weightTarget').GetValue())
        htBef[-1].Scale(1.0 / htBef[-1].Integral())

        hoBef.append(odf.Histo1D((f'original_before_{var}', f'original_before_{var}', NBINS, ranges[i][0], ranges[i][1]), var, 'weightOriginal').GetValue())
        hoBef[-1].Scale(1.0 / hoBef[-1].Integral())

        # ratio plot
        hRatioBef.append(TH1D(f'Ratio_before_{var}', f'Ratio_before_{var}', NBINS, ranges[i][0], ranges[i][1]))
        hRatioBef[-1].Divide(htBef[-1], hoBef[-1])

        if AllWeightName:
            # comparison after reweighting
            htAfter.append(tdf.Histo1D((f'target_after_{var}', f'target_after_{var}', NBINS, ranges[i][0], ranges[i][1]), var, 'weightTarget').GetValue())
            htAfter[-1].Scale(1.0 / htAfter[-1].Integral())

            hoAfter.append(odf.Histo1D((f'o_after_{var}', f'o_after_{var}', NBINS, ranges[i][0], ranges[i][1]), var, 'allWeightName').GetValue())
            hoAfter[-1].Scale(1.0 / hoAfter[-1].Integral())

            # ratio plot
            hRatioAfter.append(TH1D(f'Ratio_after_{var}', f'Ratio_after_{var}', NBINS, ranges[i][0], ranges[i][1]))
            hRatioAfter[-1].Divide(htAfter[-1], hoAfter[-1])

        else:
            hoAfter.append('')
            htAfter.append('')
            hRatioAfter.append('')

    # -----------set canvas--------------#
    cols = min(len(obranches), 4)  # max # of cols = 4
    rows = int(math.ceil(len(obranches) / cols))  # row block

    if AllWeightName:
        cc = TCanvas('cc', 'cc', 600 * cols, 1000 * rows)
        cc.Divide(cols, rows * 4)  # create a canvas with the correct pads

        # cc = TCanvas('cc', 'cc', 600 * nVar, 1000)
        # cc.Divide(nVar, 4)  # create a canvas with the correct pads
    else:
        cc = TCanvas('cc', 'cc', 600 * nVar, 500 * rows)
        cc.Divide(cols, rows * 2)  # create a canvas with the correct pads

        # cc = TCanvas('cc', 'cc', 600 * nVar, 500)
        # cc.Divide(nVar, 2)  # create a canvas with the correct pads

    def helper_setPad_DistributionAndRatio(pad_Distribution, pad_Ratio):
        # pad for distribution
        pad_Distribution.SetTopMargin(0.1)
        pad_Distribution.SetBottomMargin(0)
        pad_Distribution.SetLeftMargin(0.15)
        pad_Distribution.SetRightMargin(0.15)
        # pad for ratio
        pad_Ratio.SetBottomMargin(0.35)
        pad_Ratio.SetTopMargin(0)
        pad_Ratio.SetLeftMargin(0.15)
        pad_Ratio.SetRightMargin(0.15)

    #########################################
    # -----------set Pad--------------#
    if AllWeightName:
        # compare both before and after reweighting
        # comparison after reweighting

        for i, var in enumerate(obranches):
            Pad_id_ori_main = 4 * cols * (i // cols) + i % cols + 0 * cols + 1
            Pad_id_ori_ratio = 4 * cols * (i // cols) + i % cols + 1 * cols + 1
            Pad_id_after_main = 4 * cols * (i // cols) + i % cols + 2 * cols + 1
            Pad_id_after_ratio = 4 * cols * (i // cols) + i % cols + 3 * cols + 1

            intervalHeight = float(1) / rows  # block
            i_row = i // cols
            zeroPoint_y = 1 - (i_row + 1) * intervalHeight

            cc.GetPad(Pad_id_ori_main).SetPad(float(i % cols) / cols, zeroPoint_y + 0.7 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 1 * intervalHeight)  # pad for main distribution
            cc.GetPad(Pad_id_ori_ratio).SetPad(float(i % cols) / cols, zeroPoint_y + 0.5 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 0.7 * intervalHeight)  # pad for ratio
            helper_setPad_DistributionAndRatio(cc.GetPad(Pad_id_ori_main), cc.GetPad(Pad_id_ori_ratio))

            # comparison after reweighting
            cc.GetPad(Pad_id_after_main).SetPad(float(i % cols) / cols, zeroPoint_y + 0.2 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 0.5 * intervalHeight)  # pad for main distribution
            cc.GetPad(Pad_id_after_ratio).SetPad(float(i % cols) / cols, zeroPoint_y + 0 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 0.2 * intervalHeight)  # pad for ratio
            helper_setPad_DistributionAndRatio(cc.GetPad(Pad_id_after_main), cc.GetPad(Pad_id_after_ratio))

    else:
        # compare before reweighting only
        for i, var in enumerate(obranches):
            Pad_id_ori_main = 2 * cols * (i // cols) + i % cols + 0 * cols + 1
            Pad_id_ori_ratio = 2 * cols * (i // cols) + i % cols + 1 * cols + 1

            intervalHeight = float(1) / rows  # block
            i_row = i // cols
            zeroPoint_y = 1 - (i_row + 1) * intervalHeight

            cc.GetPad(Pad_id_ori_main).SetPad(float(i % cols) / cols, zeroPoint_y + 0.7 / 2 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 1 * intervalHeight)  # pad for main distribution
            cc.GetPad(Pad_id_ori_ratio).SetPad(float(i % cols) / cols, zeroPoint_y + 0.5 * intervalHeight, float(i % cols + 1) / cols, zeroPoint_y + 0.7 / 2 * intervalHeight)  # pad for ratio
            helper_setPad_DistributionAndRatio(cc.GetPad(Pad_id_ori_main), cc.GetPad(Pad_id_ori_ratio))

    # -----------draw plots--------------#
    for i, var in enumerate(obranches):
        if AllWeightName:
            cc.cd(4 * cols * (i // cols) + i % cols + 0 * cols + 1)
        else:
            cc.cd(2 * cols * (i // cols) + i % cols + 0 * cols + 1)

        # cc.cd(i + 1)

        print(var, NBINS, ranges[i][0], ranges[i][1], var, WeightTarget)

        htBef[i].Draw()
        helper_set_histStyle_ht(htBef[i])

        hoBef[i].Draw('same')
        htBef[i].SetMaximum(max(htBef[i].GetMaximum(), hoBef[i].GetMaximum()) + 0.5 * (max(htBef[i].GetMaximum(), hoBef[i].GetMaximum()) - min(htBef[i].GetMinimum(), hoBef[i].GetMinimum())))

        legs.append(TLegend(0.22, 0.73, 0.85, 0.88))
        legs[-1].SetNColumns(2)
        legs[-1].SetTextFont(133)
        legs[-1].SetTextSize(26)
        legs[-1].SetFillStyle(0)
        legs[-1].SetBorderSize(0)

        print(LableDict[ModeOriginal])
        print(LableDict)
        legs[-1].AddEntry(hoBef[i], LableDict[ModeOriginal], 'lp')
        legs[-1].AddEntry(htBef[i], LableDict[ModeTarget], 'lp')
        legs[-1].Draw()

        # ratio plot
        if AllWeightName:
            cc.cd(4 * cols * (i // cols) + i % cols + 1 * cols + 1)
        else:
            cc.cd(2 * cols * (i // cols) + i % cols + 1 * cols + 1)

        # cc.cd(i + nVar + 1)
        hRatioBef[i].Divide(htBef[i], hoBef[i])
        hRatioBef[i].Draw()
        helper_set_hRatio(hRatioBef[i], xTitles[i], "#frac{N(" + LableDict[ModeTarget] + ")}{N(" + LableDict[ModeOriginal] + ")}")
        RatioLines.append(get_RatioLines(f"fbef{var}", (hRatioBef[i].GetXaxis().GetXmin(), hRatioBef[i].GetXaxis().GetXmax())))
        RatioLines[-1].Draw("same")

        if AllWeightName:
            # comparison after reweighting
            cc.cd(4 * cols * (i // cols) + i % cols + 2 * cols + 1)
            # cc.cd(i + 2 * nVar + 1)

            htAfter[i].Draw()
            htAfter[i].GetXaxis().SetNoExponent()
            helper_set_histStyle_ht(htAfter[i])

            hoAfter[i].Draw('same')
            htAfter[i].SetMaximum(
                max(htAfter[i].GetMaximum(), hoAfter[i].GetMaximum()) + 0.3 * (max(htAfter[i].GetMaximum(), hoAfter[i].GetMaximum()) - min(htAfter[i].GetMinimum(), hoAfter[i].GetMinimum()))
            )
            # ratio plot
            cc.cd(4 * cols * (i // cols) + i % cols + 3 * cols + 1)
            # cc.cd(i + 3 * nVar + 1)

            hRatioAfter[i].Draw()
            helper_set_hRatio(hRatioAfter[i], xTitles[i], "#frac{N(" + LableDict[ModeTarget] + ")}{N(" + LableDict[ModeOriginal] + ")}")
            RatioLines.append(get_RatioLines(f"fafter{var}", (hRatioAfter[i].GetXaxis().GetXmin(), hRatioAfter[i].GetXaxis().GetXmax())))
            RatioLines[-1].Draw("same")

    output_file = f'{OutputDir}/WeightingPlots_{mode}.pdf'
    # cc.Draw()
    cc.SaveAs(output_file)
    print(f"Create plot {output_file}")

    ##If asked for: Plot individual variables
    if PlotIndividual:
        for i, var in enumerate(obranches):
            varN = var.replace(',', '-').replace('(', '').replace(')', '')
            MakeWeightingPlot(
                hoBef[i],
                htBef[i],
                hoAfter[i],
                htAfter[i],
                xTitles[i],
                ranges[i],
                NBINS,
                LableDict[ModeOriginal],
                LableDict[ModeTarget],
                f"W. {LableDict[ModeOriginal]}",
                LableDict[ModeTarget],
                f'{OutputDir}/WeightingPlot_{mode}_{varN}.pdf',
                scale=0.9,
            )


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('--VariablesFiles', type=str, help='Single Path to the file with variable lists or concerned variables, separated by comma. e.g. B_PT,B_P')
    parser.add_argument('--mode', type=str, default='', help='name of the selection in yaml')

    parser.add_argument('--Selections', type=str, default='', help='cut expression')
    parser.add_argument('--WeightOriginal', type=str, default="", dest='WeightOriginal')
    parser.add_argument('--WeightTarget', type=str, default="", dest='WeightTarget')
    parser.add_argument(
        '--Ranges',
        type=str,
        default="",
        help="Corresponding range. Three ways to set this argument.  1)'auto': just use pre-defined ranges as within percentage of [0.1%, 99.9%] sorted for certain variable.  2)'auto+1,99': use customized ranges as within certain percentage, here refers to [1%, 99%] sorted for certain variable.  3)'990,1050+0,500000+0,40000': use fully customized ranges, defined for each variable considered and separated by '+'.",
    )
    parser.add_argument('--ModeOriginal', type=str, default="", dest='ModeOriginal')
    parser.add_argument('--ModeTarget', type=str, default="", dest='ModeTarget')
    parser.add_argument(
        '--XTitles', type=str, default="", help="corresponding titles of x-axis.  1) '': just use the same name as branch name  2)'p^K,p^#pi': specify certain xTitles for each branch considered"
    )

    parser.add_argument('--WeightFilesOriginal', type=str, default="", dest='WeightFilesOriginal', help='Path of original file with weight branch added, separate with comma.')
    parser.add_argument('--WeightTreesOriginal', type=str, default="DecayTree", dest='WeightTreesOriginal', help='Tree name of original file')
    parser.add_argument('--WeightFilesTarget', type=str, default="", dest='WeightFilesTarget', help='Path of target file with weight branch added, separate with comma.')
    parser.add_argument('--WeightTreesTarget', type=str, default="DecayTree", dest='WeightTreesTarget', help='Tree name of target file')

    parser.add_argument('--AllWeightName', type=str, default="", help='All weights which apply to original file to show the power of reweighting')
    parser.add_argument('--PlotIndividual', type=int, default=1, choices=[0, 1], help='whether plot individual plots')
    parser.add_argument('--OutputDir', type=str, default="./tmp", help='Directory of output plots')

    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    MakeWeightingPlot_all(**vars(args))


if __name__ == '__main__':
    main()
