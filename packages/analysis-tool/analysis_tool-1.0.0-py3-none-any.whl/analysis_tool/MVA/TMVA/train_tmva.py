'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 14:01:50 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-16 15:37:45 +0200
FilePath     : train_tmva.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

#!/usr/bin/env python
# @(#)root/tmva $Id$
# ------------------------------------------------------------------------------ #
# Project      : TMVA - a Root-integrated toolkit for multivariate data analysis #
# Package      : TMVA                                                            #
# Python script: TMVAClassification.py                                           #
#                                                                                #
# This python script provides examples for the training and testing of all the   #
# TMVA classifiers through PyROOT.                                               #
#                                                                                #
# The Application works similarly, please see:                                   #
#    TMVA/macros/TMVAClassificationApplication.C                                 #
# For regression, see:                                                           #
#    TMVA/macros/TMVARegression.C                                                #
#    TMVA/macros/TMVARegressionpplication.C                                      #
# and translate to python as done here.                                          #
#                                                                                #
# As input data is used a toy-MC sample consisting of four Gaussian-distributed  #
# and linearly correlated input variables.                                       #
#                                                                                #
# The methods to be used can be switched on and off via the prompt command, for  #
# example:                                                                       #
#                                                                                #
#    python TMVAClassification.py --methods Fisher,Likelihood                    #
#                                                                                #
# The output file "TMVA.root" can be analysed with the use of dedicated          #
# macros (simply say: root -l <../macros/macro.C>), which can be conveniently    #
# invoked through a GUI that will appear at the end of the run of this macro.    #
#                                                                                #
# for help type "python TMVAClassification.py --help"                            #
# ------------------------------------------------------------------------------ #

# --------------------------------------------
# Standard python import
from typing import List, Dict, Union, Optional, Any
import os
import sys
from pathlib import Path
import argparse
import yaml
from array import array
from ROOT import TCut, ROOT, RDataFrame, gROOT, TMVA, TFile
from rich import print as rprint

from .ConfigureEachMethod import ConfigureEachMethod

MODULO_LARGE_VALUE = 10000


def read_from_yaml(mode: str, selection_files: List[str]) -> Dict[str, Any]:
    """
    Read BDT configuration from yaml files.

    Args:
        mode: Analysis mode from the yaml configuration
        selection_files: List of yaml files containing the configuration

    Returns:
        Dictionary with BDT configuration parameters
    """
    bdt_dict = {}
    for file in selection_files:
        with open(file, 'r') as stream:
            bdt_dict |= yaml.safe_load(stream)[mode]
    return bdt_dict


def train_tmva(
    signal_file: str,
    signal_tree_name: str,
    signal_weight: Optional[str],
    background_file: str,
    background_tree_name: str,
    background_weight: Optional[str],
    output_dir: str,
    bdt_vars: List[str],
    mode: str,
    bdt_method_name: Union[str, List[str]],
    num_folds: Union[str, int],
    train_fraction: float = 0.7,
) -> None:
    """
    Train a TMVA classifier with the given signal and background samples.

    Args:
        signal_file: Path to the ROOT file containing signal events
        signal_tree_name: Name of the TTree containing signal events
        signal_weight: Expression for signal event weights
        background_file: Path to the ROOT file containing background events
        background_tree_name: Name of the TTree containing background events
        background_weight: Expression for background event weights
        output_dir: Directory to store output files
        bdt_vars: List of yaml files with variable definitions
        mode: Name of the selection in yaml
        bdt_method_name: Name(s) of the TMVA method(s) to use
        num_folds: Number of folds for cross-validation
        train_fraction: Fraction of events to use for training (default: 0.7)
    """
    gROOT.SetBatch(1)
    # Check ROOT version
    if gROOT.GetVersionCode() >= 332288 and gROOT.GetVersionCode() < 332544:
        rprint("*** You are running ROOT version 5.18, which has problems in PyROOT such that TMVA")
        rprint("*** does not run properly (function calls with enums in the argument are ignored).")
        rprint("*** Solution: either use CINT or a C++ compiled version (see TMVA/macros or TMVA/examples),")
        rprint("*** or use another ROOT version (e.g., ROOT 5.19).")
        sys.exit(1)

    # Ensure bdt_method_name is a list
    bdt_method_name_list: List[str] = [bdt_method_name] if not isinstance(bdt_method_name, list) else bdt_method_name

    num_folds: int = int(num_folds)
    if num_folds > 0:
        # Define available methods for cross-validation
        available_method_names: List[str] = ['BDT', 'BDTG', 'BDTG0', 'BDTG1', 'BDTG3', 'MLP']
        # Check if all selected methods are available
        for method_name in bdt_method_name_list:
            if method_name not in available_method_names:
                rprint(f"*** Folding method is implemented only for {available_method_names}, but {method_name} was requested")
                sys.exit(1)

    # Read the cuts and branches from all input files
    bdt_conversion: Dict[str, Any] = read_from_yaml(mode, bdt_vars)

    # Create output directory and file
    os.makedirs(output_dir, exist_ok=True)
    output_file: str = os.path.join(output_dir, 'TMVA.root')
    outputFile = TFile(output_file, 'RECREATE')

    # Create DataLoader instance
    dataloader = TMVA.DataLoader("dataset")

    # Create instance of TMVA factory (see TMVA/macros/TMVAClassification.C for more factory options)
    # All TMVA output can be suppressed by removing the "!" (not) in
    # front of the "Silent" argument in the option string
    dataloader = TMVA.DataLoader("dataset")
    if num_folds > 0:
        cvOptions: List[str] = [
            "!V",
            "!Silent",
            "Color",
            "DrawProgressBar",
            "Transformations=I;D;P;G,D",
            "AnalysisType=Classification",
            "FoldFileOutput",
            "NumWorkerProcs=0",
            f"NumFolds={num_folds}",
            "SplitType=Deterministic",
            "SplitExpr=int(fabs([eventNumber]))%int([NumFolds])",
        ]
        cvOptions_str = ':'.join(cvOptions)

        factory = TMVA.CrossValidation(
            "TMVACrossValidation",
            dataloader,
            outputFile,
            cvOptions_str,
        )
        # "!V:!Silent:Color:DrawProgressBar:Transformations=I;D;P;G,D:AnalysisType=Classification"
        # ":FoldFileOutput:NumWorkerProcs=0"
        # ":NumFolds=" + str(num_folds) + ":SplitType=Deterministic:SplitExpr=int(fabs([eventNumber]))%int([NumFolds])",
        # )
    else:
        cOptions: List[str] = [
            "!V",
            "!Silent",
            "Color",
            "DrawProgressBar",
            "Transformations=I;D;P;G,D",
            "AnalysisType=Classification",
        ]
        cOptions_str = ':'.join(cOptions)
        factory = TMVA.Factory("TMVAClassification", outputFile, cOptions_str)
        # "!V:!Silent:Color:DrawProgressBar:Transformations=I;D;P;G,D:AnalysisType=Classification")

    # Set verbosity
    factory.SetVerbose(True)

    # Configure TMVA IO names
    (TMVA.gConfig().GetIONames()).fWeightFileDirPrefix = output_dir
    (TMVA.gConfig().GetIONames()).fWeightFileDir = "/"

    #    (TMVA.gConfig().GetIONames()).fWeightFileDir = output_dir

    # If you wish to modify default settings
    # (please check "src/Config.h" to see all available global options)
    #    gConfig().GetVariablePlotting()).fTimesRMS = 8.0
    #    gConfig().GetIONames()).fWeightFileDir = "myWeightDirectory"

    # Define the input variables that shall be used for the classifier training
    # note that you may also use variable expressions, such as: "3*var1/var2*abs(var3)"
    # [all types of expressions that can also be parsed by TTree::Draw( "expression" )]

    # Define input variables for training
    mva_vars: Dict[str, array] = {}
    for var in bdt_conversion.keys():
        mva_vars[var] = array('f', [-999])
        dataloader.AddVariable(var)

    # Add spectator variables for cross-validation
    if num_folds > 0:
        #        dataloader.AddSpectator("runNumber:=runNumber%1000")
        dataloader.AddSpectator(f"eventNumber := eventNumber % {MODULO_LARGE_VALUE}")

    #        dataloader.AddSpectator("eventNumber := eventNumber % 1000", 'I')
    # You can add so-called "Spectator variables", which are not used in the MVA training,
    # but will appear in the final "TestTree" produced by TMVA. This TestTree will contain the
    # input variables, the response values of all trained MVAs, and the spectator variables
    # factory.AddSpectator( "eventNumber:=EventNumber",  "eventNumber", "units", 'F' )
    # factory.AddSpectator( "runNumber:=runNumber",  "runNumber", "units", 'F' )

    # Open input files
    sigFile = TFile.Open(signal_file)
    bkgFile = TFile.Open(background_file)

    # Get the signal and background trees
    signal = sigFile.Get(signal_tree_name)
    background = bkgFile.Get(background_tree_name)

    # Calculate training/testing split
    kTrainSubsample: float = float(train_fraction)
    kSigNumTrainEvents: int = int(kTrainSubsample * signal.GetEntries())
    kBkgNumTrainEvents: int = int(kTrainSubsample * background.GetEntries())
    # kNumTrainEvents = 100000;

    kSigNumTestEvents: int = int(signal.GetEntries() - kSigNumTrainEvents)
    kBkgNumTestEvents: int = int(background.GetEntries() - kBkgNumTrainEvents)
    # kNumTestEvents  = 600000;

    # Print configuration information
    prefix: str = "TMVACrossValidation" if num_folds > 0 else "TMVAClassification"
    rprint(f"--- {prefix}      : Using signal file: {signal_file}")
    rprint(f"--- {prefix}      : Using background file: {background_file}")
    rprint(f"--- {prefix}      : Using number of events: ")
    rprint(f"--- {prefix}      : Train signal:     {kSigNumTrainEvents}")
    rprint(f"--- {prefix}      : Train background: {kBkgNumTrainEvents}")
    rprint(f"--- {prefix}      : Test signal:      {kSigNumTestEvents}")
    rprint(f"--- {prefix}      : Test background:  {kBkgNumTestEvents}")

    # Global event weights (see below for setting event-wise weights)
    signalWeight = 1.0
    backgroundWeight = 1.0

    # ====== register trees ====================================================
    #
    # the following method is the prefered one:
    # you can add an arbitrary number of signal or background trees
    dataloader.AddSignalTree(signal, signalWeight)
    dataloader.AddBackgroundTree(background, backgroundWeight)

    # To give different trees for training and testing, do as follows:
    #    factory.AddSignalTree( signalTrainingTree, signalTrainWeight, "Training" )
    #    factory.AddSignalTree( signalTestTree,     signalTestWeight,  "Test" )

    # Use the following code instead of the above two or four lines to add signal and background
    # training and test events "by hand"
    # NOTE that in this case one should not give expressions (such as "var1+var2") in the input
    #      variable definition, but simply compute the expression before adding the event
    #
    #    # --- begin ----------------------------------------------------------
    #
    # ... *** please lookup code in TMVA/macros/TMVAClassification.C ***
    #
    #    # --- end ------------------------------------------------------------
    #
    # ====== end of register trees ==============================================

    # Set individual event weights (the variables must exist in the original TTree)
    #    for signal    : factory.SetSignalWeightExpression    ("weight1*weight2");
    #    for background: factory.SetBackgroundWeightExpression("weight1*weight2");
    if signal_weight:
        dataloader.SetSignalWeightExpression(str(signal_weight))
    if background_weight:
        dataloader.SetBackgroundWeightExpression(str(background_weight))

    # Apply additional cuts on the signal and background sample.
    # example for cut: mycut = TCut( "abs(var1)<0.5 && abs(var2-0.5)<1" )
    # mycuts = TCut(""); # for example: TCut mycuts = "abs(var1)<0.5 && abs(var2-0.5)<1";
    # mycutb = TCut(""); # for example: TCut mycutb = "abs(var1)<0.5";

    # Here, the relevant variables are copied over in new, slim trees that are
    # used for TMVA training and testing
    # "SplitMode=Random" means that the input events are randomly shuffled before
    # splitting them into training and test samples
    # dataloader.PrepareTrainingAndTestTree( mycutSig, mycutBkg,
    #                                    "nTrain_Signal=0:nTrain_Background=0:SplitMode=Random:NormMode=NumEvents:!V" )

    # Prepare training and test data
    mycuts = TCut("")
    dataloader.PrepareTrainingAndTestTree(
        mycuts,
        kSigNumTrainEvents,
        kBkgNumTrainEvents,
        kSigNumTestEvents,
        kBkgNumTestEvents,
        "SplitMode=Random:NormMode=NumEvents:!V",
    )

    # TString splitExpr = "int(fabs([eventID]))%int([NumFolds])";
    # --------------------------------------------------------------------------------------------------

    # ---- Book MVA methods
    for method_name in bdt_method_name:
        ConfigureEachMethod(factory, dataloader, method_name, num_folds)
    # --------------------------------------------------------------------------------------------------

    # ---- Now you can tell the factory to train, test, and evaluate the MVAs.

    # Train MVAs
    if num_folds > 0:
        factory.Evaluate()
    else:
        factory.TrainAllMethods()

        # Test MVAs
        factory.TestAllMethods()

        # Evaluate MVAs
        factory.EvaluateAllMethods()

    # Save the output.
    outputFile.Close()

    rprint("=== wrote root file %s\n" % output_file)
    rprint("=== TMVAClassification is done!\n")

    # --------------------------------------------------------------------------------------------------
    if num_folds > 0:
        for i in range(len(bdt_method_name)):
            method_name = bdt_method_name[i]
            factory.GetResults()[i].Draw(f"{method_name} CrossValidation").SaveAs(f"{output_dir}/ROCCompare_{method_name}_kFold{num_folds}.pdf")
            factory.GetResults()[i].DrawAvgROCCurve(True, f"Avg ROC for {method_name} include kFold").SaveAs(f"{output_dir}/ROCCompare_Avg_ROC_for_{method_name}_kFold_included.pdf")
            factory.GetResults()[i].DrawAvgROCCurve(False, f"Avg ROC for {method_name} exclude kFold").SaveAs(f"{output_dir}/ROCCompare_Avg_ROC_for_{method_name}_kFold_excluded.pdf")

    # open the GUI for the result macros
    # gROOT.ProcessLine( "TMVAGui(\"%s\")" % output_file )

    # keep the ROOT thread running
    # gApplication.Run()


def get_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal-file', required=True, type=str, help='Path to the signal file')
    parser.add_argument('--signal-tree-name', default='DecayTree', type=str, help='Name of the tree')
    parser.add_argument('--signal-weight', default='1', type=str, help='Weight variable')
    parser.add_argument('--background-file', required=True, type=str, help='Path to the background file')
    parser.add_argument('--background-tree-name', default='DecayTree', type=str, help='Name of the tree')
    parser.add_argument('--background-weight', default='1', type=str, help='Weight variable')
    parser.add_argument('--output-dir', required=True, type=str, help='Output ROOT file')
    parser.add_argument('--bdt-vars', nargs='+', required=True, help='Yaml files with selection')
    parser.add_argument('--mode', required=True, type=str, help='Name of the selection in yaml')
    parser.add_argument('--bdt-method-name', nargs='+', required=True, help='Choose which BDT to apply')
    #    parser.add_argument('--bdt-method-name', default='BDTG3', help='Choose which BDT to apply')
    parser.add_argument('--num-folds', default="0", type=int, help='Number of foldings')
    parser.add_argument('--train-fraction', default="0.7", type=float, help='Fraction of events to use for training')
    return parser


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the script.

    Args:
        args: Parsed command-line arguments (if None, parse from sys.argv)
    """
    if args is None:
        args = get_parser().parse_args()
    train_tmva(**vars(args))


if __name__ == '__main__':
    main()
