# python-3
# coding: utf-8
'''
Script Name: BuildConsolidatedFeaturesFile.py

Created date : Sunday, 27th March

Author : Sreejith Menon

Description : 
buildFeatureFl(input file,output file)
Reads from a csv file (taken as a parameter) containing a list of image GIDs. 

Extracts the below features from the IBEIS dataset:
1. nid
2. names
3. species_texts
4. sex_texts
5. age_months_est
6. exemplar_flags
7. quality_texts

Outputs 3 files in the same directory as the outFL directory
File 1 : Map of all images and their annotation IDs (csv)
File 2 : Annotation ID's and their features (csv)
File 3 : Image GID, annotation ID's and their features (csv)
File 4 : Image GID, annotation ID's and their features (json)
'''

import csv
import GetPropertiesAPI as GP
import importlib
import json
#importlib.reload(GP) # un-comment if there are any changes made to API
import sys
import math

def printCompltnPercent(percentComplete):
	i = int(percentComplete)
	sys.stdout.write('\r')
    # the exact output you're looking for:
	sys.stdout.write("[%-100s] %d%%" % ('='*i, i))
	sys.stdout.flush()

def writeCsvFromDict(header,inDict,outFL):
	writeFL = open(outFL,'w')
	writer = csv.writer(writeFL)
	writer.writerow(header)

	for key in inDict.keys():
		if inDict[key] == None:
			value = ["NONE"]
		else:
			value = inDict[key]
			writer.writerow([key] + value)
	
	writeFL.close()

# Original Microsoft Tagging API output is a R list, 
# This method parses the data into python readable form and dumps the output into a JSON.
def genJsonFromMSAIData(flName,outFlNm):
    data = []
    with open(flName) as openFl:
        for row in openFl:
            data.append(row)


    cleanData = []
    for row in data:
        cleanData.append(row.replace("\\","").replace('"\n',""))

    apiResultsDict = {}

    for i in range(1,len(cleanData)):
        key,value = cleanData[i].split("\t")
        value = value.replace('"{"tags"','{"tags"')
        key = key.replace('"','')
        apiResultsDict[key] = json.loads(value)

    json.dump(apiResultsDict,open(outFlNm,"w"),indent=4)
    
    return None

# Logic for reading data from the consolidatedHITResults file - changed
# The input for the below method will be a csv file/list with all the image GID's for which the features have to be extracted.
def buildFeatureFl(inp,outFL,isInpFl = True):
	allGID = []

	if isInpFl:
		reader = csv.reader(open(inp,"r"))
		for row in reader:
			allGID.append(row)
	else: #input is provided as a list
		allGID = inp 

	#aids = GP.getAnnotID(allGID)
	# Extracts all the annotation ID's from IBEIS
	#GidAidMap = {allGID[i] : aids[i] for i in range(0,len(allGID))}
	gidInd = 0
	GidAidMap = {}
	for gid in allGID:
		aid = GP.getAnnotID(int(gid))
		GidAidMap[gid] = [aid]
		gidInd += 1
		percentComplete = gidInd * 100 / len(allGID)
		if math.floor(percentComplete) %5 == 0:
			printCompltnPercent(percentComplete)
		print()
		
	print("Extracted all annotation ID's for selected images.")

	# filter out all the non-NONE annotation ids
	aidList = []
	for gid in GidAidMap.keys():
		for aid in filter(lambda x: x != None,GidAidMap[gid]):
			aidList = aidList + aid

	# Extracts all feature info based on annotation ID's from IBEIS
	features = {}
	print("Features to be extracted for %d annotation IDs" %len(aidList))
	nids = GP.getImageFeature(aidList,"name/rowid")
	names = GP.getImageFeature(aidList,"name/text")
	species_texts = GP.getImageFeature(aidList,"species/text")
	sex_texts = GP.getImageFeature(aidList,"sex/text")
	age_months = GP.getImageFeature(aidList,"age/months")
	exemplar_flags = GP.getImageFeature(aidList,"exemplar")
	quality_texts = GP.getImageFeature(aidList,"quality/text")
	yaw_texts = GP.getImageFeature(aidList,"yaw/text")
	image_contrib_tags = GP.getImageFeature(aidList,"image/contributor/tag")

	features = {aidList[i] : [nids[i],names[i],species_texts[i],sex_texts[i],
				GP.getAgeFeatureReadableFmt(age_months[i]),str(exemplar_flags[i]),
				quality_texts[i],yaw_texts[i],image_contrib_tags[i]] 
				for i in range(0,len(aidList))}
	# for aid in aidList:
	# 	nid = GP.getImageFeature(aid,"name/rowid")
	# 	features[aid] = [nid]
	# 	names = GP.getImageFeature(aid,"name/text")
	# 	features[aid].append(names)
	# 	spec_text = GP.getImageFeature(aid,"species/text")
	# 	features[aid].append(spec_text)
	# 	sex_text = GP.getImageFeature(aid,"sex/text")
	# 	features[aid].append(sex_text)
	# 	est_age = GP.getImageFeature(aid,"age/months")
	# 	features[aid].append(GP.getAgeFeatureReadableFmt(est_age))
	# 	exemplar = GP.getImageFeature(aid,"exemplar")
	# 	features[aid].append(list(map(str,exemplar))) # needed to convert the flags to string
	# 	qual_text = GP.getImageFeature(aid,"quality/text")
	# 	features[aid].append(qual_text)
	# 	yaw_text = GP.getImageFeature(aid,"yaw/text")
	# 	features[aid].append(yaw_text)
	# 	contrib_tag = GP.getImageFeature(aid,"image/contributor/tag")
	# 	features[aid].append(contrib_tag)
	# 	aidInd += 1
	# 	percentComplete = aidInd * 100 / len(aidList)
	# 	if math.floor(percentComplete) %5 == 0:
	# 		printCompltnPercent(percentComplete)
	print()
	print("All features extracted.")

	# Build the all combined file
	GidAidFeatures = {}
	for gid in GidAidMap.keys():
		if GidAidMap[gid][0] == None:
			GidAidFeatures[gid] = None
		else:
			GidAidFeatures[gid] = []
			for aid in GidAidMap.get(gid)[0]:
				newAidFeatures = {}
				newAidFeatures[aid] = features[aid]
				GidAidFeatures[gid].append(newAidFeatures)

	writeFLTitle,writeFLExt = outFL.split('.csv')
	writeFLExt = 'csv'
	writeFLGidAidFl = writeFLTitle + "_gid_aid_map." + writeFLExt
	writeFLAidFeatureFl = writeFLTitle + "_aid_features." + writeFLExt
	writeFLGidAidFeatureFl = writeFLTitle + "_gid_aid_features." + writeFLExt

	# Snippet for writing image GID - annotation ID map to a csv file
	head = ['GID','ANNOTATION_ID']
	writeCsvFromDict(head,GidAidMap,writeFLGidAidFl)

	head = ['ANNOTATION_ID','NID','NAME','SPECIES','SEX','AGE_MONTHS','EXEMPLAR_FLAG','IMAGE_QUALITY','IMAGE_YAW']
	writeCsvFromDict(head,features,writeFLAidFeatureFl)

	head = ['GID','ANNOTATION_ID','FEATURES']
	writeCsvFromDict(head,GidAidFeatures,writeFLGidAidFeatureFl) 

	outFL = open((writeFLTitle + "_gid_aid_map.json"),"w")
	json.dump(GidAidMap,outFL,indent=4)
	outFL.close()

	outFL = open((writeFLTitle + "_aid_features.json"),"w")
	json.dump(features,outFL,indent=4)
	outFL.close()

	outFL = open((writeFLTitle + "_gid_aid_features.json"),"w")
	json.dump(GidAidFeatures,outFL,indent=4)
	outFL.close()

	print("Script completed.")

