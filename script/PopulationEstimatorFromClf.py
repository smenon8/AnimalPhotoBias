# python-3

# Population Estimator Implementation on predicted shared dataset. 
# Author: Sreejith Menon (smenon8@uic.edu)
# Script creation date: Sept 30, 2016


import MarkRecapHelper as MR
import pandas as pd
import json
import ClassiferHelperAPI as CH
import DeriveFinalResultSet as DRS
import importlib
import sys
import cufflinks as cf # this is necessary to link pandas to plotly
cf.go_online()
import plotly.graph_objs as go
importlib.reload(CH)
import htmltag as HT
import random
import argparse

inExifFl,inGidAidMapFl,inAidFtrFl = "../data/imgs_exif_data_full.json","../data/full_gid_aid_map.json","../data/full_aid_features.json"
layout = go.Layout(
    title="Number of images shared(k) versus estimated population",
    titlefont = dict(size=15),
    xaxis=dict(
        title="Number of images shared(k)",
        titlefont = dict(
        size=15),
        showticklabels=True,
        tickangle=35,
        tickfont=dict(
        size=9,
        color='black')
        ),
    yaxis=dict(
        title="Estimated Population",
        titlefont = dict(
        size=15),
        showticklabels=True,
        tickfont=dict(
        size=9,
        color='black')
        )
    )

def trainTestClf(train_data_fl,test_data_fl,clf,attribType,infoGainFl=None,methArgs=None):
    # Create training data
    allAttribs = CH.genAllAttribs(train_data_fl,attribType,infoGainFl)
    train_data= CH.getMasterData(train_data_fl)
    
    # Create testing data
    test_data= CH.getMasterData(test_data_fl)
    testObj = CH.createDataFlDict(test_data,allAttribs,0.8,'Test')

    testDf =  pd.DataFrame(testObj).transpose()

    # Build classifier
    clfObj = CH.buildBinClassifier(train_data,allAttribs,0.0,80,clf,methArgs.get(clf,None))

    # Set testing data and run classifier
    testDataFeatures = testDf[clfObj.train_x.columns]
    clfObj.setTestAttrib('test_x',testDataFeatures)
    clfObj.runClf(computeMetrics=False)

    prediction_results = {list(clfObj.test_x.index)[i] : clfObj.preds[i] for i in range(len(clfObj.test_x.index))}    

    return clfObj, prediction_results

def biasedCoinFlipper(p):
    return 1 if random.random() < p else 0

def trainTestRgrs(train_data_fl,test_data_fl,methodName,attribType,infoGainFl=None,methArgs=None):
    allAttribs = CH.genAllAttribs(train_data_fl,attribType,infoGainFl)
    
    test_data= CH.getMasterData(test_data_fl)
    testObj = CH.createDataFlDict(test_data,allAttribs,0.8,'Test')
    
    testDf =  pd.DataFrame(testObj).transpose()

    rgrObj = CH.buildRegrMod(train_data_fl,allAttribs,0.0,methodName,kwargs=methArgs.get(methodName,None))

    testDataFeatures = testDf[rgrObj.train_x.columns]
    rgrObj.setTestAttrib('test_x',testDataFeatures)
    rgrObj.runRgr(computeMetrics=False, removeOutliers=True)
    
    prediction_results = {list(rgrObj.test_x.index)[i] : rgrObj.preds[i] for i in range(len(rgrObj.test_x.index))}    

    return rgrObj, prediction_results


def estimatePopulation(prediction_results,inExifFl,inGidAidMapFl,inAidFtrFl):
    df = pd.DataFrame(prediction_results,index=['share']).transpose().reset_index()
    df.columns = ['GID','share']
    df.to_csv("/tmp/PredictionResults.csv",index=False)

    days = {'2015-03-01' : 1,
        '2015-03-02' : 2 }

    # Entire population estimate (includes giraffes and zebras)
    nidMarkRecapSet = MR.genNidMarkRecapDict(inExifFl,
                    inGidAidMapFl,
                    inAidFtrFl,
                    "/tmp/PredictionResults.csv",
                    days,
                    shareData='classifier')
    marks_all,recaptures_all,population_all = MR.applyMarkRecap(nidMarkRecapSet)

    nidMarkRecapSet = MR.genNidMarkRecapDict(inExifFl,
                    inGidAidMapFl,
                    inAidFtrFl,
                    "/tmp/PredictionResults.csv",
                    days,
                    filterBySpecies='zebra_plains',
                    shareData='classifier')
    marks_z,recaptures_z,population_z = MR.applyMarkRecap(nidMarkRecapSet)

    nidMarkRecapSet = MR.genNidMarkRecapDict(inExifFl,
                    inGidAidMapFl,
                    inAidFtrFl,
                    "/tmp/PredictionResults.csv",
                    days,
                    filterBySpecies='giraffe_masai',
                    shareData='classifier')
    marks_g,recaptures_g,population_g = MR.applyMarkRecap(nidMarkRecapSet)

    return {'all' : population_all , 
            'zebras' : population_z , 'giraffes' : population_g}

def kSharesPerContribAfterCoinFlip(prediction_results,inExifFl,inGidAidMapFl,inAidFtrFl,genk,randomShare = False):
    gidContribDct = DRS.getCountingLogic(inGidAidMapFl,inAidFtrFl,'CONTRIBUTOR',False)

    sdCards = {}
    for key in gidContribDct.keys():
        sdCards[gidContribDct[key][0]] = sdCards.get(gidContribDct[key][0],[]) + [key]

    sdCardSorted = {}
    for contrib in sdCards.keys():
        sdCardSorted[contrib] = sorted(sdCards[contrib],key=lambda x : prediction_results.get(x,0),reverse=True)

    if randomShare:
        for contrib in sdCardSorted.keys():
            sdCardSorted[contrib] = random.sample(sdCardSorted[contrib],len(sdCardSorted[contrib]))

    k = genk()
    
    predictions_k = {}
    for contrib in sdCardSorted.keys():
        pctCnt = 0
        exitCntr = 0
        while pctCnt < k and pctCnt < len(sdCardSorted[contrib]) and exitCntr <= 500:
            nextImg = sdCardSorted[contrib][pctCnt]
            exitCntr += 1
            flip = biasedCoinFlipper(prediction_results.get(nextImg,0)/100)
            if flip == 1:
                predictions_k[nextImg] = 1
                pctCnt += 1

    return estimatePopulation(predictions_k,inExifFl,inGidAidMapFl,inAidFtrFl)

# synthetic experiment #1 and #2
def kSharesPerContributor(prediction_probabs,inExifFl,inGidAidMapFl,inAidFtrFl,genk, randomShare=False):
    gidContribDct = DRS.getCountingLogic(inGidAidMapFl,inAidFtrFl,'CONTRIBUTOR',False)

    sdCards = {}
    for key in gidContribDct.keys():
        sdCards[gidContribDct[key][0]] = sdCards.get(gidContribDct[key][0],[]) + [key]

    sdCardSorted = {}
    for contrib in sdCards.keys():
        sdCardSorted[contrib] = sorted(sdCards[contrib],key=lambda x : prediction_probabs.get(x,0),reverse=True)

    if randomShare:
        for contrib in sdCardSorted.keys():
            sdCardSorted[contrib] = random.sample(sdCardSorted[contrib],len(sdCardSorted[contrib]))

    # selecting the top k scores as shared
    predictions_k = {gid : 1 for contrib in sdCardSorted.keys() for gid in sdCardSorted[contrib][:genk()]}

    return estimatePopulation(predictions_k,inExifFl,inGidAidMapFl,inAidFtrFl)

def shareAbvThreshold(prediction_probabs,inExifFl,inGidAidMapFl,inAidFtrFl,threshold,randomShare=None):
    gidContribDct = DRS.getCountingLogic(inGidAidMapFl,inAidFtrFl,'CONTRIBUTOR',False)

    sdCards = {}
    for key in gidContribDct.keys():
        sdCards[gidContribDct[key][0]] = sdCards.get(gidContribDct[key][0],[]) + [key]

    sdCardSorted = {}
    for contrib in sdCards.keys():
        sdCardSorted[contrib] = sorted(sdCards[contrib],key=lambda x : prediction_probabs.get(x,0),reverse=True)

    threshold = threshold()
    for contrib in sdCardSorted.keys():
        sdCardSorted[contrib] = list(filter(lambda x : prediction_probabs.get(x,0) >= threshold,sdCards[contrib]))

    # selecting the top k scores as shared
    predictions_k = {gid : 1 for contrib in sdCardSorted.keys() for gid in sdCardSorted[contrib]}

    return estimatePopulation(predictions_k,inExifFl,inGidAidMapFl,inAidFtrFl)

def runSyntheticExpts(isClf, methTypes, attribTypes, krange, methArgs, thresholdMeth = False, randomShare = False):
    for meth in methTypes:
        for attrib in attribTypes:
            print("Starting to run %s classifer on test data\nAttribute Selection Method : %s" %(meth,attrib))
            if isClf:
                trainTestMeth = trainTestClf
            else:
                trainTestMeth = trainTestRgrs

            methObj,predResults = trainTestMeth("../FinalResults/ImgShrRnkListWithTags.csv",
                                "../data/full_gid_aid_ftr_agg.csv",
                                meth,
                                attrib,
                                infoGainFl="../data/infoGainsExpt2.csv",
                                methArgs = methArgs
                                )
            if thresholdMeth:
                flNm = str("../FinalResults/"+ meth + "_" + attrib + "_thresholded")
            else:
                if randomShare:
                    flNm = str("../FinalResults/"+ meth + "_" + attrib + "_kSharesRandom")
                else:
                    flNm = str("../FinalResults/"+ meth + "_" + attrib + "_kShares")

            if isClf:
                predictions = {list(methObj.test_x.index)[i] : methObj.predProbabs[i] for i in range(len(methObj.test_x.index))}
                sharesMethod = kSharesPerContributor
            else:
                predictions = predResults
                if thresholdMeth:
                    sharesMethod = shareAbvThreshold
                else:
                    sharesMethod = kSharesPerContribAfterCoinFlip

            if randomShare:
                hdr = "Population Estimates when contributor shares k random photos using %s and attribute selection method %s" %(meth,attrib)
            else:
                if thresholdMeth:
                    hdr = "Population Estimates when contributors share all images above threshold using %s and attribute selection method %s" %(meth,attrib)
                else:
                    hdr = "Population Estimates with k shares per contributor using %s and attribute selection method %s" %(meth,attrib)

            print("Starting population estimation experiments")
            
            fixedK = {k : sharesMethod(predictions,inExifFl,inGidAidMapFl,inAidFtrFl,lambda : k,randomShare=randomShare) for k in krange}
            print("Population estimation experiments complete")
            
            df = pd.DataFrame(fixedK).transpose().reset_index()
            
            if not thresholdMeth:
                df.columns = ['num_images','all','giraffes','zebras']
                df.index = df['num_images']
                df.drop(['num_images'],1,inplace=True)
            else:
                df.columns = ['threshold','all','giraffes','zebras']
                df.index = df['threshold']
                df.drop(['threshold'],1,inplace=True)

            df.to_csv(str(flNm+".csv"))
            df_html = df.to_html(index=True)
            randomized = sharesMethod(predictions,inExifFl,inGidAidMapFl,inAidFtrFl,lambda : random.randint(min(krange),max(krange)))
            df['Randomized_all'] = randomized['all']
            df['Randomized_giraffe'] = randomized['giraffes']
            df['Randomized_zebras'] = randomized['zebras']
            
            if thresholdMeth:
                fig1 = df.iplot(kind='line',layout=layout,filename=str(meth + "_" + attrib + "_thresholded"))
            else:
                if randomShare:
                    fig1 = df.iplot(kind='line',layout=layout,filename=str(meth + "_" + attrib + "_kSharesRandom"))
                else:
                    fig1 = df.iplot(kind='line',layout=layout,filename=str(meth + "_" + attrib + "_kShares"))


            fullFl = HT.HTML(HT.body(HT.h2(hdr),
                            HT.HTML(df_html),
                            HT.HTML(fig1.embed_code)         
                    ))

            outputFile = open(str(flNm+".html"),"w")
            outputFile.write(fullFl)
            outputFile.close()
            print("Classification testing complete %s : %s" %(meth,attrib))
            print()

def runSyntheticExptsRgr(inExifFl, inGidAidMapFl, inAidFtrFl, krange, thresholdMeth=False, randomShare=False):
    rgrTypes = ['linear','ridge','lasso','svr','dtree_regressor']
    attribTypes = ['sparse','non_sparse','non_zero','abv_mean']

    regrArgs = {'linear' : {'fit_intercept' : True},
            'ridge' : {'fit_intercept' : True},
            'lasso' : {'fit_intercept' : True},
            'svr' : {'fit_intercept' : True},
            'dtree_regressor' : {'fit_intercept' : True}}

    runSyntheticExpts(False, rgrTypes, attribTypes, krange, regrArgs, thresholdMeth=thresholdMeth, randomShare=randomShare)


def runSyntheticExptsClf(inExifFl, inGidAidMapFl, inAidFtrFl, krange, randomShare=False):
    clfTypes = ['bayesian','logistic','svm','dtree','random_forests','ada_boost']
    clfTypes = ['ada_boost']
    attribTypes = ['non_sparse','non_zero','abv_mean']
    methArgs = {'dummy' : {'strategy' : 'most_frequent'},
            'bayesian' : {'fit_prior' : True},
            'logistic' : {'penalty' : 'l2'},
            'svm' : {'kernel' : 'rbf','probability' : True},
            'dtree' : {'criterion' : 'entropy'},
            'random_forests' : {'n_estimators' : 10 },
            'ada_boost' : {'n_estimators' : 50 }}

    runSyntheticExpts(True, clfTypes, attribTypes, krange, methArgs, randomShare=randomShare)

def buildErrPlots(clfOrRgr, thresholdMeth=False, randomShare=False):
    if clfOrRgr == 'clf':
        algTypes = ['bayesian','logistic','svm','dtree','random_forests','ada_boost']
    else:
        algTypes = ['linear','ridge','lasso','svr','dtree_regressor']
    attribTypes = ['sparse','non_sparse','non_zero','abv_mean']
    flNms = [str(alg + "_" + attrib) for alg in algTypes for attrib in attribTypes]

    if thresholdMeth:
        suffix = "_thresholded.csv"
        hdr = "threshold"
        if clfOrRgr == 'clf':
            titleSuffix = "classifiers thresholded"
        else:
            titleSuffix = "regressors thresholded"
    else:
        hdr = "num_images"
        if randomShare:
            suffix = "_kSharesRandom.csv"
            if clfOrRgr == 'clf':
                titleSuffix = "classifiers random choices"
            else:
                titleSuffix = "regressors random choices"
        else:
            suffix = "_kSharesbottom.csv"
            if clfOrRgr == 'clf':
                titleSuffix = "classifiers top k choices"
            else:
                titleSuffix = "regressors bottom k choices"

    df = pd.DataFrame.from_csv(str("../FinalResults/"+flNms[0]+suffix)).reset_index()
    df.columns = list(map(lambda x : str(x + "_" + flNms[0]) if x != hdr else x,list(df.columns)))
    for i in range(1,len(flNms)):
        df1 = pd.DataFrame.from_csv(str("../FinalResults/"+flNms[i]+suffix)).reset_index()
        df1.columns = list(map(lambda x : str(x + "_" + flNms[i]) if x != hdr else x,list(df1.columns)))
        df = pd.DataFrame.merge(df,df1,on=hdr)

    df.index = df[hdr]
    df.drop([hdr],1,inplace=True)

    for col in df.columns:
        if 'all' in col:
            df[str(col+'_err')] = (3620 - df[col]) / 36.20
        elif 'zebras' in col:
            df[str(col+'_err')] = (3468 - df[col]) / 34.68
        elif 'giraffes' in col:
            df[str(col+'_err')] = (177 - df[col]) / 1.77

    figs=[]
    errorCols = [col for col in df.columns if 'err' in col]
    df = df[errorCols]

    for alg in algTypes:
        algCol = [col for col in df.columns if alg in col]
        algDf = df[algCol]
        titleAlg = "All %s %s" %(alg,titleSuffix)
        figs.append(algDf.iplot(kind='line',title=titleAlg))

    for attrib in attribTypes:
        attribCol = [col for col in df.columns if attrib in col]
        attribDf = df[attribCol]
        titleAttrib = "All %s %s" %(attrib,titleSuffix)
        figs.append(algDf.iplot(kind='line',title=titleAttrib))

    figCodes = [fig.embed_code for fig in figs]
    return figCodes

def populationEstimatorFileGen():
    clfTypes = ['bayesian','logistic','svm','dtree','random_forests','ada_boost']
    attribTypes = ['sparse','non_sparse','non_zero','abv_mean']
    
    kwargsDict = {'dummy' : {'strategy' : 'most_frequent'},
            'bayesian' : {'fit_prior' : True},
            'logistic' : {'penalty' : 'l2'},
            'svm' : {'kernel' : 'rbf','probability' : True},
            'dtree' : {'criterion' : 'entropy'},
            'random_forests' : {'n_estimators' : 10 },
            'ada_boost' : {'n_estimators' : 50 }}

    if len(sys.argv) > 1:
        outFlNm = sys.argv[1]
    else:
        outFlNm = "/tmp/PopulationEstimatorFromClf.dump.json"

    estimates = []
    for clf in clfTypes:
        for attribType in attribTypes:
            print("Classifier : %s" %clf)
            print("Attribute selection method : %s" %attribType)
            clfObj,predResults = trainTestClf("../FinalResults/ImgShrRnkListWithTags.csv",
                     "../data/full_gid_aid_ftr_agg.csv",
                     clf,
                     attribType,
                     "../data/infoGainsExpt2.csv",
                     kwargsDict)
            thisObjhead = {'Classifier' : clf , 'Attribute' : attribType,'shared_images_count' : int(sum(clfObj.preds))}
            thisObj = estimatePopulation(predResults,
                            "../data/imgs_exif_data_full.json",
                            "../data/full_gid_aid_map.json",
                            "../data/full_aid_features.json")

            estimates.append({**thisObjhead,**thisObj})
            print("Complete")
            print()

    with open(outFlNm,"w") as jsonFl:
        json.dump(estimates,jsonFl,indent=4)

def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cr','--clfOrRgr', help='Classifier method or regressor to be used', required=True)
    parser.add_argument('-t','--threshold', help='Threshold method, if set will be used', required=False)
    parser.add_argument('-r','--random', help='Share any random images, if set will be used', required=False)
    args = vars(parser.parse_args())

    if args["clfOrRgr"] == 'clf' and args["random"] != None:
        print("Running classifiers with random image selections")
        runSyntheticExptsClf(inExifFl,inGidAidMapFl,inAidFtrFl,range(2,75),randomShare=True)

    if args["clfOrRgr"] == 'clf' and args["random"] == None:
        print("Running classifiers with top k image selections")
        runSyntheticExptsClf(inExifFl,inGidAidMapFl,inAidFtrFl,range(2,75))

    if args["clfOrRgr"] == 'rgr' and args["random"] != None:
        print("Running regressors with random image selections")
        runSyntheticExptsRgr(inExifFl,inGidAidMapFl,inAidFtrFl,range(2,75),randomShare = True)
    
    if args["clfOrRgr"] == 'rgr' and args["random"] == None and args["threshold"] != None:
        print("Running regressors with top image above thresholds")
        runSyntheticExptsRgr(inExifFl,inGidAidMapFl,inAidFtrFl,range(40,90,5),thresholdMeth = True)
    
    if args["clfOrRgr"] == 'rgr' and args["random"] == None and args["threshold"] == None:
        print("Running regressors with top k image selections")
        runSyntheticExptsRgr(inExifFl,inGidAidMapFl,inAidFtrFl,range(2,75),thresholdMeth = False)

if __name__ == "__main__":
    # __main__()
    pass