# python-3
# Regression Capsule Class
# In the same lines as ClassifierCapsuleClass
from sklearn.metrics import mean_absolute_error, mean_squared_error
from BaseCapsuleClass import BaseCapsule
from collections import OrderedDict
import pandas as pd

class RegressionCapsule(BaseCapsule):
	def __init__(self,clfObj,methodName,splitPercent,train_x,train_y,test_x,test_y):
		BaseCapsule.__init__(self,clfObj,methodName,splitPercent,train_x,train_y,test_x,test_y)
		self.residues = None

	def evalClassifierPerf(self):
		self.abserr = mean_absolute_error(self.test_y,self.preds)
		self.sqerr = mean_squared_error(self.test_y,self.preds)
		if not self.test_y.empty:
			self.residues = [list(self.test_y)[i] - self.preds[i] for i in range(len(self.preds))]

	def removeOutliers(self):
		idxs = [i for i in range(len(self.preds)) if self.preds[i] > 100 or self.preds[i] < 0]
		
		idxList = list(self.test_x.index)
		predDict = OrderedDict()
		for i in range(len(idxList)):
		    predDict[idxList[i]] =  self.preds[i]
		df = pd.DataFrame(predDict,index=['Predictions']).transpose()

		self.test_x.drop(self.test_x.index[idxs], inplace=True)

		if self.test_y != None:
			if not self.test_y.empty:
				self.test_y.drop(self.test_y.index[idxs], inplace=True)
		df.drop(df.index[idxs], inplace=True)
		
		self.preds = list(df['Predictions'])

		print("Number of outliers identified: %d" %len(idxs))
		print(len(self.test_x),len(self.preds))

	def runRgr(self,computeMetrics=True,removeOutliers=True):
		BaseCapsule.run(self)
		
		if removeOutliers:
			self.removeOutliers()

		if computeMetrics:
			return self.evalClassifierPerf()
		else:
			return 0