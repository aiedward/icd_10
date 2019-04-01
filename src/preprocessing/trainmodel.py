import mysql.connector as sql
import pandas as pd
from pathlib import Path
import numpy as np

from sklearn import preprocessing
from sklearn import model_selection
from sklearn.utils import shuffle
from sklearn.metrics import confusion_matrix,classification_report
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.naive_bayes import MultinomialNB
from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import PassiveAggressiveClassifier
from xgboost import XGBClassifier

import os

def get_dataset(trainingset, validation_size):
	n = len(trainingset.columns)-1
	array = trainingset.values
	X = array[:,0:n]
	Y = array[:,n]
	seed = 7
	X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size, random_state=seed)
	X_train, Y_train = shuffle(X_train, Y_train, random_state=seed)
	return X_train, X_validation, Y_train, Y_validation

def eval(testset_path,model):
	X_train, X_validation, Y_train, Y_validation = get_dataset(testset, 0.0)
	p = model.predict(X_train)
	cf = confusion_matrix(Y_train, p)
	print(cf)
	cr = classification_report(Y_train, p)
	print(cr)

def get_target_class(p,name):
	p = '../../secret/data/drug/'+name
	value = []
	for df in  pd.read_csv(p, chunksize=10000):
		v = df[feature].unique().tolist()
		value = value + v
		value = list(set(value))
		value.sort()
		print(len(value))

	df = pd.DataFrame.from_dict({feature:value})
	df.to_csv('../../secret/data/test/'+name+'_class.csv')
	print(df)



def train_model(filename):

	#c = MultinomialNB()
	#c = BernoulliNB()
	#c = PassiveAggressiveClassifier(n_jobs=-1, warm_start=True)
	#c = SGDClassifier(loss='log')
	#c = Perceptron(n_jobs=-1,warm_start=True)

	#c = SVC()
	
	
	p = '../../secret/data/trainingset/'+filename+'.csv'
	targets = []
	for df in  pd.read_csv(p, chunksize=100000, index_col=0):
		df['icd10'] = df['icd10'].apply(str)
		v = df['icd10'].unique().tolist()
		targets = targets + v
		targets = list(set(targets))
	targets.sort()

	if not os.path.exists('../../secret/data/model/')
		os.makedirs('../../secret/data/model/')
	
	if not os.path.exists('../../secret/data/model/'+filename)
		os.makedirs('../../secret/data/model/'+filename)

	for target in targets:
		data = None
		chunk = 10000
		c = XGBClassifier(max_depth=100)

		for df in  pd.read_csv(p, chunksize=chunk, index_col=0):
			df.loc[:, ~df.columns.str.contains('^Unnamed')]
			df.drop(['TXN'], axis=1, inplace=True)

			t = df[df['icd10']==target]
			nt = df[df['icd10']!=target]
			nt = nt.assign(icd10 = 'not_'+target)
			if len(nt) > len(t):
				nt = nt.sample(frac=1).reset_index(drop=True)
				nt = nt.head(len(t))
			t = t.append(nt, ignore_index = True)
			t = t.reset_index(drop=True)
			if data is None:
				data = t
			else:
				data = data.append(t).reset_index(drop=True)
			#print(data)
		if len(data) >= 100:
			print(data)
			'''
			X_train, X_validation, Y_train, Y_validation = get_dataset(data, 0.1)
			c.fit(X_train, Y_train)
			pre = c.predict(X_validation)
			print(target)
			cf = confusion_matrix(Y_validation, pre)
			print(cf)
			cr = classification_report(Y_validation, pre)
			print(cr)
			'''

