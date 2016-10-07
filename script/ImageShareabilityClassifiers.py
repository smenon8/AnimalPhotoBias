# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 18:37:45 2016

@author: sreejithmenon

Author: Sreejith Menon (smenon8@uic.edu)
General Description:
    Multiple features are extracted per image.
    The features are majorly classified as:
        Bilogical features like age, species, sex
        Ecological features like yaw, view_point
        Image EXIF/Quality data: unixtime, latitude, longitude, quality
        Tags generated by Microsoft Image tagging API
        Image Contributor - Sparse attribute
        Individual animals (NID)
    Based on these features mutliple classification algorithms are implemented and the metrics are evaluated. The aim of the classification algorithms is to predict given features, will a certain image be shared/not shared on a social media platform.
    The ClassifierHelperAPI has off-the-shelf implementations from sk-learn library and uses a Classifier Object to store the metrics of each classifier.
    The performance metrics evaluated are:
        Accuracy - Number of correct predictions in the test data
        Precision
        Recall
        F1 score
        Absolute Error
        AUC
        Squared Error - Not displayed currently
        Zero One Hinge Loss - Not displayed currently
"""

import ClassiferHelperAPI as CH
import importlib
import numpy as np
import pandas as pd
importlib.reload(CH)
from ast import literal_eval
import plotly.plotly as py
import htmltag as HT
import cufflinks as cf # this is necessary to link pandas to plotly
cf.go_online()

minSplit = 0.2
maxSplit = 0.6

data= CH.getMasterData("../FinalResults/ImgShrRnkListWithTags.csv")  
methods = ['dummy','bayesian','logistic','svm','dtree','random_forests','ada_boost']
kwargsDict = {'dummy' : {'strategy' : 'most_frequent'},
            'bayesian' : None,
            'logistic' : None,
            'svm' : {'kernel' : 'rbf','probability' : True},
            'dtree' : None,
            'random_forests' : None,
            'ada_boost' : None}
for attribsType in ['sparse','non_sparse','non_zero','abv_mean']:
    print("Classifier training started for %s" %attribsType)  

    allAttribs = CH.genAllAttribs("../FinalResults/ImgShrRnkListWithTags.csv",attribsType,"../data/infoGainsExpt2.csv")
    
    classifiers = []
    for method in methods:
        for i in np.arange(minSplit,maxSplit,0.1): # i is the test percent
            clfObj = CH.buildBinClassifier(data,allAttribs,1-i,80,method,kwargsDict[clf])
            clfObj.runClf()
            classifiers.append(clfObj)
            
    printableClfs = []

    for clf in classifiers:
        printableClfs.append(dict(literal_eval(clf.__str__())))
        
    df = pd.DataFrame(printableClfs)
    df = df[['methodName','splitPercent','accScore','precision','recall','f1Score','auc','sqerr']]
    df.columns = ['Classifier','Train-Test Split','Accuracy','Precision','Recall','F1 score','AUC','Squared Error']
    df.to_csv("../ClassifierResults/extrmClfMetrics_%s.csv" %attribsType,index=False)

    # Will take up valuable Plot.ly plots per day. Limited to 50 plots per day.
    # changes to file name important
    iFrameBlock = []
    for i in np.arange(minSplit,maxSplit,0.1):
        df1 = df[(df['Train-Test Split']==1-i)]
        df1.index = df1['Classifier']
        df1 = df1[['Accuracy','Precision','Recall','F1 score','AUC','Squared Error']].transpose()
        fig = df1.iplot(kind='bar',filename=str('Train-Test_Split_Ratio %s %f' %(attribsType,i)),title=str('Train-Test Split Ratio: %f' %i))
        iFrameBlock.append(fig.embed_code)

    flNm = "../ClassifierResults/performanceComparison_%s.html" %attribsType
    with open(flNm,"w") as perf:
        perf.write(HT.h1("Performance Comparisons of Classifiers with %s Attributes." %attribsType))
        for row in iFrameBlock:
            perf.write(HT.HTML(row))
    
    print("Classifier training complete for %s" %attribsType)
    print()
    