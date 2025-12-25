'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-04-11 09:51:11 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-11 09:52:35 +0200
FilePath     : ConfigureEachMethod.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

# Standard python import
from typing import List, Dict, Union, Optional, Any
import sys
import argparse
import yaml
from array import array
from ROOT import TCut, ROOT, RDataFrame, gROOT, TMVA, TFile


def ConfigureEachMethod(factory, dataloader, bdt_method_name: str, num_folds: int):
    # ---- Book MVA methods
    #
    # please lookup the various method configuration options in the corresponding cxx files, eg:
    # src/MethoCuts.cxx, etc, or here: http://tmva.sourceforge.net/optionRef.html
    # it is possible to preset ranges in the option string in which the cut optimisation should be done:
    # "...:CutRangeMin[2]=-1:CutRangeMax[2]=1"...", where [2] is the third input variable

    # Cut optimisation
    if bdt_method_name == "Cuts":
        factory.BookMethod(dataloader, TMVA.Types.kCuts, "Cuts", "!H:!V:FitMethod=MC:EffSel:SampleSize=200000:VarProp=FSmart")

    if bdt_method_name == "CutsD":
        factory.BookMethod(dataloader, TMVA.Types.kCuts, "CutsD", "!H:!V:FitMethod=MC:EffSel:SampleSize=200000:VarProp=FSmart:VarTransform=Decorrelate")

    if bdt_method_name == "CutsPCA":
        factory.BookMethod(dataloader, TMVA.Types.kCuts, "CutsPCA", "!H:!V:FitMethod=MC:EffSel:SampleSize=200000:VarProp=FSmart:VarTransform=PCA")

    if bdt_method_name == "CutsGA":
        factory.BookMethod(
            dataloader, TMVA.Types.kCuts, "CutsGA", "H:!V:FitMethod=GA:CutRangeMin[0]=-10:CutRangeMax[0]=10:VarProp[1]=FMax:EffSel:Steps=30:Cycles=3:PopSize=400:SC_steps=10:SC_rate=5:SC_factor=0.95"
        )

    if bdt_method_name == "CutsSA":
        factory.BookMethod(dataloader, TMVA.Types.kCuts, "CutsSA", "!H:!V:FitMethod=SA:EffSel:MaxCalls=150000:KernelTemp=IncAdaptive:InitialTemp=1e+6:MinTemp=1e-6:Eps=1e-10:UseDefaultScale")

    # Likelihood ("naive Bayes estimator")
    if bdt_method_name == "Likelihood":
        factory.BookMethod(dataloader, TMVA.Types.kLikelihood, "Likelihood", "H:!V:!TransformOutput:PDFInterpol=Spline2:NSmoothSig[0]=20:NSmoothBkg[0]=20:NSmoothBkg[1]=10:NSmooth=1:NAvEvtPerBin=50")

    # Decorrelated likelihood
    if bdt_method_name == "LikelihoodD":
        factory.BookMethod(
            dataloader, TMVA.Types.kLikelihood, "LikelihoodD", "!H:!V:TransformOutput:PDFInterpol=Spline2:NSmoothSig[0]=20:NSmoothBkg[0]=20:NSmooth=5:NAvEvtPerBin=50:VarTransform=Decorrelate"
        )

    # PCA-transformed likelihood
    if bdt_method_name == "LikelihoodPCA":
        factory.BookMethod(
            dataloader, TMVA.Types.kLikelihood, "LikelihoodPCA", "!H:!V:!TransformOutput:PDFInterpol=Spline2:NSmoothSig[0]=20:NSmoothBkg[0]=20:NSmooth=5:NAvEvtPerBin=50:VarTransform=PCA"
        )

    # Use a kernel density estimator to approximate the PDFs
    if bdt_method_name == "LikelihoodKDE":
        factory.BookMethod(
            dataloader, TMVA.Types.kLikelihood, "LikelihoodKDE", "!H:!V:!TransformOutput:PDFInterpol=KDE:KDEtype=Gauss:KDEiter=Adaptive:KDEFineFactor=0.3:KDEborder=None:NAvEvtPerBin=50"
        )

    # Use a variable-dependent mix of splines and kernel density estimator
    if bdt_method_name == "LikelihoodMIX":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kLikelihood,
            "LikelihoodMIX",
            "!H:!V:!TransformOutput:PDFInterpolSig[0]=KDE:PDFInterpolBkg[0]=KDE:PDFInterpolSig[1]=KDE:PDFInterpolBkg[1]=KDE:PDFInterpolSig[2]=Spline2:PDFInterpolBkg[2]=Spline2:PDFInterpolSig[3]=Spline2:PDFInterpolBkg[3]=Spline2:KDEtype=Gauss:KDEiter=Nonadaptive:KDEborder=None:NAvEvtPerBin=50",
        )

    # Test the multi-dimensional probability density estimator
    # here are the options strings for the MinMax and RMS methods, respectively:
    #      "!H:!V:VolumeRangeMode=MinMax:DeltaFrac=0.2:KernelEstimator=Gauss:GaussSigma=0.3" );
    #      "!H:!V:VolumeRangeMode=RMS:DeltaFrac=3:KernelEstimator=Gauss:GaussSigma=0.3" );
    if bdt_method_name == "PDERS":
        factory.BookMethod(dataloader, TMVA.Types.kPDERS, "PDERS", "!H:!V:NormTree=T:VolumeRangeMode=Adaptive:KernelEstimator=Gauss:GaussSigma=0.3:NEventsMin=400:NEventsMax=600")

    if bdt_method_name == "PDERSD":
        factory.BookMethod(dataloader, TMVA.Types.kPDERS, "PDERSD", "!H:!V:VolumeRangeMode=Adaptive:KernelEstimator=Gauss:GaussSigma=0.3:NEventsMin=400:NEventsMax=600:VarTransform=Decorrelate")

    if bdt_method_name == "PDERSPCA":
        factory.BookMethod(dataloader, TMVA.Types.kPDERS, "PDERSPCA", "!H:!V:VolumeRangeMode=Adaptive:KernelEstimator=Gauss:GaussSigma=0.3:NEventsMin=400:NEventsMax=600:VarTransform=PCA")

    # Multi-dimensional likelihood estimator using self-adapting phase-space binning
    if bdt_method_name == "PDEFoam":
        factory.BookMethod(dataloader, TMVA.Types.kPDEFoam, "PDEFoam", "!H:!V:SigBgSeparate=F:TailCut=0.001:VolFrac=0.0666:nActiveCells=500:nSampl=2000:nBin=5:Nmin=100:Kernel=None:Compress=T")

    if bdt_method_name == "PDEFoamBoost":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kPDEFoam,
            "PDEFoamBoost",
            "!H:!V:Boost_Num=30:Boost_Transform=linear:SigBgSeparate=F:MaxDepth=4:UseYesNoCell=T:DTLogic=MisClassificationError:FillFoamWithOrigWeights=F:TailCut=0:nActiveCells=500:nBin=20:Nmin=400:Kernel=None:Compress=T",
        )

    # K-Nearest Neighbour classifier (KNN)
    if bdt_method_name == "KNN":
        factory.BookMethod(dataloader, TMVA.Types.kKNN, "KNN", "H:nkNN=20:ScaleFrac=0.8:SigmaFact=1.0:Kernel=Gaus:UseKernel=F:UseWeight=T:!Trim")

    # H-Matrix (chi2-squared) method
    if bdt_method_name == "HMatrix":
        factory.BookMethod(dataloader, TMVA.Types.kHMatrix, "HMatrix", "!H:!V:VarTransform=None")

    # Linear discriminant (same as Fisher discriminant)
    if bdt_method_name == "LD":
        factory.BookMethod(dataloader, TMVA.Types.kLD, "LD", "H:!V:VarTransform=None:CreateMVAPdfs:PDFInterpolMVAPdf=Spline2:NbinsMVAPdf=50:NsmoothMVAPdf=10")

    # Fisher discriminant (same as LD)
    if bdt_method_name == "Fisher":
        factory.BookMethod(dataloader, TMVA.Types.kFisher, "Fisher", "H:!V:Fisher:VarTransform=None:CreateMVAPdfs:PDFInterpolMVAPdf=Spline2:NbinsMVAPdf=50:NsmoothMVAPdf=10")

    # Fisher with Gauss-transformed input variables
    if bdt_method_name == "FisherG":
        factory.BookMethod(dataloader, TMVA.Types.kFisher, "FisherG", "H:!V:VarTransform=Gauss")

    # Composite classifier: ensemble (tree) of boosted Fisher classifiers
    if bdt_method_name == "BoostedFisher":
        factory.BookMethod(dataloader, TMVA.Types.kFisher, "BoostedFisher", "H:!V:Boost_Num=20:Boost_Transform=log:Boost_Type=AdaBoost:Boost_AdaBoostBeta=0.2:!Boost_DetailedMonitoring")

    # Function discrimination analysis (FDA) -- test of various fitters - the recommended one is Minuit (or GA or SA)
    if bdt_method_name == "FDA_MC":
        factory.BookMethod(
            dataloader, TMVA.Types.kFDA, "FDA_MC", "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=MC:SampleSize=100000:Sigma=0.1"
        )

    if bdt_method_name == "FDA_GA":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kFDA,
            "FDA_GA",
            "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=GA:PopSize=300:Cycles=3:Steps=20:Trim=True:SaveBestGen=1",
        )

    if bdt_method_name == "FDA_SA":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kFDA,
            "FDA_SA",
            "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=SA:MaxCalls=15000:KernelTemp=IncAdaptive:InitialTemp=1e+6:MinTemp=1e-6:Eps=1e-10:UseDefaultScale",
        )

    if bdt_method_name == "FDA_MT":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kFDA,
            "FDA_MT",
            "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=MINUIT:ErrorLevel=1:PrintLevel=-1:FitStrategy=2:UseImprove:UseMinos:SetBatch",
        )

    if bdt_method_name == "FDA_GAMT":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kFDA,
            "FDA_GAMT",
            "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=GA:Converger=MINUIT:ErrorLevel=1:PrintLevel=-1:FitStrategy=0:!UseImprove:!UseMinos:SetBatch:Cycles=1:PopSize=5:Steps=5:Trim",
        )

    if bdt_method_name == "FDA_MCMT":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kFDA,
            "FDA_MCMT",
            "H:!V:Formula=(0)+(1)*x0+(2)*x1+(3)*x2+(4)*x3:ParRanges=(-1,1)(-10,10);(-10,10);(-10,10);(-10,10):FitMethod=MC:Converger=MINUIT:ErrorLevel=1:PrintLevel=-1:FitStrategy=0:!UseImprove:!UseMinos:SetBatch:SampleSize=20",
        )

    # TMVA ANN: MLP (recommended ANN) -- all ANNs in TMVA are Multilayer Perceptrons
    if bdt_method_name == "MLP":
        if num_folds > 0:
            factory.BookMethod(
                TMVA.Types.kMLP,
                "MLP",
                "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:!UseRegulator:Sampling=0.5:SamplingEpoch=0.8:ConvergenceTests=11:ConvergenceImprove=1e-6",
            )
        else:
            factory.BookMethod(
                dataloader,
                TMVA.Types.kMLP,
                "MLP",
                "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:!UseRegulator:Sampling=0.5:SamplingEpoch=0.8:ConvergenceTests=11:ConvergenceImprove=1e-6",
            )

    if bdt_method_name == "MLPBFGS":
        factory.BookMethod(dataloader, TMVA.Types.kMLP, "MLPBFGS", "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:TrainingMethod=BFGS:!UseRegulator")

    if bdt_method_name == "MLPBNN":
        # factory.BookMethod( TMVA.Types.kMLP, "MLPBNN", "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:TrainingMethod=BFGS:UseRegulator" ) # BFGS training with bayesian regulators
        factory.BookMethod(dataloader, TMVA.Types.kMLP, "MLPBNN", "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:TrainingMethod=BP:UseRegulator")

    # Multi-architecture DNN implementation.
    if bdt_method_name == "DNN":
        # General layout.
        layoutString = "Layout=TANH|128,TANH|128,TANH|128,LINEAR"

        # Training strategies.
        training0 = (
            "LearningRate=1e-1,Momentum=0.9,Repetitions=1,"
            "ConvergenceSteps=20,BatchSize=256,TestRepetitions=10,"
            "WeightDecay=1e-4,Regularization=L2,"
            "DropConfig=0.0+0.5+0.5+0.5, Multithreading=True"
        )
        training1 = (
            "LearningRate=1e-2,Momentum=0.9,Repetitions=1,"
            "ConvergenceSteps=20,BatchSize=256,TestRepetitions=10,"
            "WeightDecay=1e-4,Regularization=L2,"
            "DropConfig=0.0+0.0+0.0+0.0, Multithreading=True"
        )
        training2 = (
            "LearningRate=1e-3,Momentum=0.0,Repetitions=1,"
            "ConvergenceSteps=20,BatchSize=256,TestRepetitions=10,"
            "WeightDecay=1e-4,Regularization=L2,"
            "DropConfig=0.0+0.0+0.0+0.0, Multithreading=True"
        )
        trainingStrategyString = "TrainingStrategy="
        trainingStrategyString += f"{training0}|{training1}|{training2}"

        # General Options.
        dnnOptions = "!H:V:ErrorStrategy=CROSSENTROPY:VarTransform=N:" "WeightInitialization=XAVIERUNIFORM"
        dnnOptions.Append(":")
        dnnOptions.Append(layoutString)
        dnnOptions.Append(":")
        dnnOptions.Append(trainingStrategyString)

        # Standard implementation, no dependencies.
        stdOptions = f"{dnnOptions}:Architecture=STANDARD"
        factory.BookMethod(dataloader, TMVA.Types.kDNN, "DNN", stdOptions)

        # Cuda implementation.
        if bdt_method_name == "DNN_GPU":
            gpuOptions = f"{dnnOptions}:Architecture=GPU"
            factory.BookMethod(dataloader, TMVA.Types.kDNN, "DNN GPU", gpuOptions)

        # Multi-core CPU implementation.
        if bdt_method_name == "DNN_CPU":
            cpuOptions = f"{dnnOptions}:Architecture=CPU"
            factory.BookMethod(dataloader, TMVA.Types.kDNN, "DNN CPU", cpuOptions)

    # CF(Clermont-Ferrand)ANN
    if bdt_method_name == "CFMlpANN":
        factory.BookMethod(dataloader, TMVA.Types.kCFMlpANN, "CFMlpANN", "!H:!V:NCycles=2000:HiddenLayers=N+1,N")  # n_cycles:#nodes:#nodes:...

    # Tmlp(Root)ANN
    if bdt_method_name == "TMlpANN":
        factory.BookMethod(dataloader, TMVA.Types.kTMlpANN, "TMlpANN", "!H:!V:NCycles=200:HiddenLayers=N+1,N:LearningMethod=BFGS:ValidationFraction=0.3")  # n_cycles:#nodes:#nodes:...

    # Support Vector Machine
    if bdt_method_name == "SVM":
        factory.BookMethod(dataloader, TMVA.Types.kSVM, "SVM", "Gamma=0.25:Tol=0.001:VarTransform=Norm")

    # Boosted Decision Trees
    if bdt_method_name == "BDTG":
        if num_folds > 0:
            factory.BookMethod(TMVA.Types.kBDT, "BDTG", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=20:MaxDepth=3")
        else:
            factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=20:MaxDepth=3")
    if bdt_method_name == "BDTG0":
        if num_folds > 0:
            factory.BookMethod(
                TMVA.Types.kBDT,
                "BDTG0",
                "!H:!V:NTrees=1000:BoostType=Grad:Shrinkage=0.30:UseBaggedBoost:GradBaggingFraction=0.6:SeparationType=GiniIndex:nCuts=20:PruneMethod=CostComplexity:PruneStrength=50:MaxDepth=2",
            )
        else:
            factory.BookMethod(
                dataloader,
                TMVA.Types.kBDT,
                "BDTG0",
                "!H:!V:NTrees=1000:BoostType=Grad:Shrinkage=0.30:UseBaggedBoost:GradBaggingFraction=0.6:SeparationType=GiniIndex:nCuts=20:PruneMethod=CostComplexity:PruneStrength=50:MaxDepth=2",
            )
    if bdt_method_name == "BDTG1":
        if num_folds > 0:
            factory.BookMethod(TMVA.Types.kBDT, "BDTG1", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=1000:MaxDepth=3")
        else:
            factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG1", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=1000:MaxDepth=3")
    if bdt_method_name == "BDTG3":
        if num_folds > 0:
            factory.BookMethod(TMVA.Types.kBDT, "BDTG3", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.30:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=20:MaxDepth=6")
        else:
            factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTG3", "!H:!V:NTrees=1000:MinNodeSize=2.5%:BoostType=Grad:Shrinkage=0.30:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=20:MaxDepth=6")
    if bdt_method_name == "BDT":
        if num_folds > 0:
            factory.BookMethod(
                TMVA.Types.kBDT, "BDT", "!H:!V:NTrees=850:MinNodeSize=2.5%:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:UseBaggedBoost:BaggedSampleFraction=0.5:SeparationType=GiniIndex:nCuts=20"
            )
        else:
            factory.BookMethod(
                dataloader,
                TMVA.Types.kBDT,
                "BDT",
                "!H:!V:NTrees=850:MinNodeSize=2.5%:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:UseBaggedBoost:BaggedSampleFraction=0.5:SeparationType=GiniIndex:nCuts=20",
            )
    if bdt_method_name == "BDT1":
        if num_folds > 0:
            factory.BookMethod(
                TMVA.Types.kBDT, "BDT1", "!H:!V:NTrees=850:MinNodeSize=2.5%:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:UseBaggedBoost:BaggedSampleFraction=0.5:SeparationType=GiniIndex:nCuts=-1"
            )
        else:
            factory.BookMethod(
                dataloader,
                TMVA.Types.kBDT,
                "BDT1",
                "!H:!V:NTrees=850:MinNodeSize=2.5%:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:UseBaggedBoost:BaggedSampleFraction=0.5:SeparationType=GiniIndex:nCuts=-1",
            )

    if bdt_method_name == "BDTB":
        factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTB", "!H:!V:NTrees=400:BoostType=Bagging:SeparationType=GiniIndex:nCuts=20")

    if bdt_method_name == "BDTD":
        factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTD", "!H:!V:NTrees=400:MinNodeSize=5%:MaxDepth=3:BoostType=AdaBoost:SeparationType=GiniIndex:nCuts=20:VarTransform=Decorrelate")

    if bdt_method_name == "BDTF":  # Allow Using Fisher discriminant in node splitting for (strong) linearly correlated variables
        factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDTF", "!H:!V:NTrees=50:MinNodeSize=2.5%:UseFisherCuts:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:SeparationType=GiniIndex:nCuts=20")

    # RuleFit -- TMVA implementation of Friedman's method
    if bdt_method_name == "RuleFit":
        factory.BookMethod(
            dataloader,
            TMVA.Types.kRuleFit,
            "RuleFit",
            "H:!V:RuleFitModule=RFTMVA:Model=ModRuleLinear:MinImp=0.001:RuleMinDist=0.001:NTrees=20:fEventsMin=0.01:fEventsMax=0.5:GDTau=-1.0:GDTauPrec=0.01:GDStep=0.01:GDNSteps=10000:GDErrScale=1.02",
        )

    # --------------------------------------------------------------------------------------------------


#    return factory
