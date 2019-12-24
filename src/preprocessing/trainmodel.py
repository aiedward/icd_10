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
from sklearn.linear_model import SGDRegressor
from sklearn.linear_model import PassiveAggressiveRegressor
from sklearn.neural_network import MLPClassifier
#from xgboost import XGBClassifier
from sklearn.cluster import MiniBatchKMeans
from sklearn.cluster import KMeans
from sklearn.cluster import Birch
from sklearn.decomposition import MiniBatchDictionaryLearning
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import cross_val_score
from sklearn.utils import resample

import os
import re
import pickle
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler, Normalizer

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.optimizers import SGD
from dask_ml.wrappers import Incremental
import lightgbm as lgb
import xgboost as xgb

from sklearn.externals import joblib
from keras.models import model_from_json
import joblib as jl
import gc
from sklearn.metrics.pairwise import cosine_similarity
'''
from creme import linear_model
from creme import naive_bayes
from creme import metrics
from creme import optim
from creme import tree
'''
import math
from sklearn.metrics import accuracy_score
from sklearn.metrics import coverage_error
from sklearn.metrics import label_ranking_average_precision_score
from sklearn.metrics import label_ranking_loss
from sklearn.decomposition import PCA

mypath = '../../secret/data/'
#mypath = '/media/bon/My Passport/data/'

def get_dataset(trainingset, validation_size):
	for name in trainingset.columns:
		if name != 'icd10' and str(trainingset[name].dtype) == 'object':
			trainingset[name] = pd.to_numeric(trainingset[name], errors='coerce')
	trainingset.fillna(0,inplace=True)
	n = len(trainingset.columns)-1
	array = trainingset.values
	X = array[:,0:n]
	Y = array[:,n]
	seed = 7
	X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size, random_state=seed)
	if validation_size == None:
		X_train = np.concatenate((X_train, X_validation))
		Y_train = np.concatenate((Y_train, Y_validation))
		X_train, Y_train = shuffle(X_train, Y_train, random_state=seed)
	return X_train, X_validation, Y_train, Y_validation

def get_testset(trainingset):
	for name in trainingset.columns:
		if name != 'icd10' and str(trainingset[name].dtype) == 'object':
			trainingset[name] = pd.to_numeric(trainingset[name], errors='coerce')
	trainingset.fillna(0,inplace=True)
	n = len(trainingset.columns)-1
	array = trainingset.values
	X = array[:,0:n]
	Y = array[:,n]

	X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, shuffle=False)
	X_train = np.concatenate((X_train, X_validation))
	Y_train = np.concatenate((Y_train, Y_validation))

	return X_train, X_validation, Y_train, Y_validation


def eval(testset_path,model):
	X_train, X_validation, Y_train, Y_validation = get_dataset(testset, 0.0)
	p = model.predict(X_train)
	cf = confusion_matrix(Y_train, p)
	print(cf)
	cr = classification_report(Y_train, p)
	print(cr)

def get_target_class(p,name):
	p = mypath+'drug/'+name
	value = []
	for df in  pd.read_csv(p, chunksize=10000):
		v = df[feature].unique().tolist()
		value = value + v
		value = list(set(value))
		value.sort()
		print(len(value))

	df = pd.DataFrame.from_dict({feature:value})
	df.to_csv(mypath+'test/'+name+'_class.csv')
	print(df)

def save_file(df,p):
	file = Path(p)
	if file.is_file():
		with open(p, 'a') as f:
			df.to_csv(f, header=False)
	else:
		df.to_csv(p)

def remove_file(p):
	file = Path(p)
	if file.is_file():
		os.remove(p)

def train_model(models, X_train, Y_train, classes):
	for m in models:
		if str(m.estimator).startswith('SGDRegressor') or str(m.estimator).startswith('PassiveAggressiveRegressor'):
			m.partial_fit(X_train, Y_train)
		else:
			m.partial_fit(X_train, Y_train, classes=classes)
			print('Loss :'+str(m.loss_))
	return models
'''
def test(m, X_validation, Y_validation):
	if str(m.estimator).startswith('SGDRegressor') or str(m.estimator).startswith('PassiveAggressiveRegressor'):
		m.partial_fit(X_train, Y_train)
	else:
		m.partial_fit(X_train, Y_train, classes=classes)

	print(m.predict(X_validation)[:len(X_validation)])
	print('Score: ',m.score(X_validation, Y_validation))
	
def dask_model(train, modelname):
	#Good for discrete feature
	#c = MultinomialNB()
	#Good for binary feature
	#c = BernoulliNB()
	#c = PassiveAggressiveClassifier(n_jobs=-1, warm_start=True)
	#c = SGDClassifier(loss='log', penalty='l2', tol=1e-3)
	#c = Perceptron(n_jobs=-1,warm_start=True)
	models = [	#Incremental(MultinomialNB(), scoring='accuracy'),
			#Incremental(PassiveAggressiveClassifier(n_jobs=-1, warm_start=True), scoring='accuracy'),
			#Incremental(SGDClassifier(loss='log', penalty='l2', tol=1e-3), scoring='accuracy'),
			#Incremental(Perceptron(n_jobs=-1,warm_start=True), scoring='accuracy'),
			#Incremental(SGDRegressor(warm_start=True), scoring='accuracy'),
			#Incremental(PassiveAggressiveRegressor(warm_start=True), scoring='accuracy'),
			Incremental(MLPClassifier())]
	#model_names = ['passive-aggrassive-classifier','sgd-classifier','perceptron','sgd-regressor','passive-aggrassive-regressor']
	model_names = ['mlpclassifier']
	#ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	chunk = 10000
	n = 0
	#inc = Incremental(c, scoring='accuracy')
	classes = pd.read_csv(mypath+'raw/icd10.csv', index_col=0).index.values
	for name in train:
		ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
			X_train = ssc.transform(X_train)
			#X_validation = ssc.transform(X_validation)
			models = train_model(models, X_train, Y_train, classes)
			n = n + chunk
			print('Train models '+name+' '+str(n))
			#break

	for i in range(len(models)):
		save_model(models[i],modelname+'_'+model_names[i])
		#test(models, X_validation, Y_validation)
		#inc.partial_fit(X_train, Y_train, classes=classes)
		#print(inc.predict(X_validation)[:len(X_validation)])
		#print('Score: ',inc.score(X_validation, Y_validation))

def eval_model(name):
	chunk = 10000
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	#model_names = ['passive-aggrassive-classifier','sgd-classifier','perceptron','sgd-regressor','passive-aggrassive-regressor']
	model_names = ['mlpclassifier']
	if not os.path.exists(mypath+'model_prediction/'):
		os.makedirs(mypath+'model_prediction/')
	for df in pd.read_csv(mypath+'testset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
		dftest = df.copy()
		dftest.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_testset(dftest)
		X_train = ssc.transform(X_train)
		#print(len(X_train))
		for modelname in model_names:
			loaded_model = pickle.load(open(mypath+'model/'+name+'_'+modelname+'.pkl', 'rb'))
			#result = loaded_model.score(X_train, Y_train)
			#print(result)
			df[modelname] = loaded_model.predict(X_train)[:len(X_train)]
		save_file(df,mypath+'model_prediction/'+name+'.csv')
		print('Predict '+name)
'''
'''
def creme_model(name):
	#Need python >= 3.6
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	chunk = 10000
	optimizer = optim.VanillaSGD(lr=0.01)
	#model = linear_model.LinearRegression(optimizer)
	model = naive_bayes.GaussianNB()
	#model = tree.MondrianTreeClassifier(lifetime=1, max_depth=100, min_samples_split=1, random_state=16)
	#model = tree.MondrianTreeRegressor(lifetime=1, max_depth=100, min_samples_split=1, random_state=16)


	y_true = []
	y_pred = []
	metric = metrics.Accuracy()

	for df in  pd.read_csv(mypath+'vec/'+name+'.csv', chunksize=chunk, index_col=0):
		df.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(df, 0.1)
		X_train = ssc.transform(X_train)
		X_validation = ssc.transform(X_validation)
		for i in range(len(X_train.tolist())):
			# Fit the linear regression
			X = dict(zip(df.columns,X_train[i])) 
			model.fit_one(X, Y_train[i])
		for i in range(len(X_validation.tolist())):
			X = dict(zip(df.columns,X_validation[i])) 
			yi_pred = model.predict_one(X)
			# Store the truth and the prediction
			y_true.append(Y_validation[i])
			y_pred.append(round(yi_pred[True].item(0)))
		acc = accuracy_score(y_true, y_pred)
		print(acc)
'''
'''
def save_history():
	files = os.listdir(mypath+'trainingset/')

	stop = False

	for filename in files:
		filename = filename.replace('.csv','')
		if stop:
			break
		print(filename)
		p = mypath+'trainingset/'+filename+'.csv'
		targets = []
		for df in  pd.read_csv(p, chunksize=100000, index_col=0):
			df['icd10'] = df['icd10'].apply(str)
			v = df['icd10'].unique().tolist()
			targets = targets + v
			targets = list(set(targets))
		targets.sort()

		if not os.path.exists(mypath+'model_performance/'):
			os.makedirs(mypath+'model_performance/')

		if not os.path.exists(mypath+'model/'):
			os.makedirs(mypath+'model/')

		if not os.path.exists(mypath+'model/'+filename):
			os.makedirs(mypath+'model/'+filename)

		regex = re.compile('[A-Z]')
		target_classes = [i for i in targets if regex.match(i)]
		
		for target in target_classes:
			if stop:
				break
			
			if not Path(mypath+'model_performance/training_record.csv').is_file():
				save_file(pd.DataFrame(columns=['feature','icd10']),mypath+'model_performance/training_record.csv')

			save_file(pd.DataFrame([[filename,target]],columns=['feature','icd10']),mypath+'model_performance/training_record.csv')
			if filename == 'L1901' and target == 'M8445':
				stop = True
'''
def scale_data(filename):
	# scale to 0 - 1 without changing the distribution pattern, outlier still affects
	mmsc = MinMaxScaler(feature_range = (0, 1))
	# (x - mean)/sd = makes mean close to 0
	ssc = StandardScaler()
	chunk = 100000
	for df in  pd.read_csv(mypath+'trainingset/vec/'+filename+'.csv', chunksize=chunk, index_col=0):
		df.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
		ssc.partial_fit(X_train)
		mmsc.partial_fit(X_train)
	print('fit scaler '+filename)

	joblib.dump(mmsc, mypath+'scaler/'+filename+'_minmaxscaler.save') 
	joblib.dump(ssc, mypath+'scaler/'+filename+'_standardscaler.save') 

def predict(testset,testvalue,ssc,regressor):
	pre = regressor.predict(testset)
	print(pre)
	#pre = ssc.inverse_transform(pre)
	plt.plot(testvalue, color = 'black', label = 'Actual icd10')
	plt.plot(pre, color = 'green', label = 'Predicted icd10')
	plt.title('Actual vs Predicted icd10')
	plt.xlabel('feature')
	plt.ylabel('value')
	plt.legend()
	plt.show()

def history_loss(loss,val_loss):
	plt.plot(loss)
	plt.plot(val_loss)
	plt.title('model train vs validation loss')
	plt.ylabel('loss')
	plt.xlabel('epoch')
	plt.legend(['train', 'validation'], loc='upper right')
	plt.show()

def save_model(model,filename):
	pkl_filename = mypath+'model/'+filename+".pkl"  
	with open(pkl_filename, 'wb') as file:  
		 pickle.dump(model, file)
	print("save model")

def save_lstm_model(model,filename):
	if not os.path.exists(mypath+'model/'):
		os.makedirs(mypath+'model/')
	# serialize model to JSON
	model_json = model.to_json()
	with open(mypath+'model/'+filename+".json", "w") as json_file:
		 json_file.write(model_json)
	# serialize weights to HDF5
	model.save_weights(mypath+'model/'+filename+".h5")
	print("save model")

def load_model(filename):
	# load json and create model
	json_file = open(mypath+'model/'+filename+'.json', 'r')
	loaded_model_json = json_file.read()
	json_file.close()
	loaded_model = model_from_json(loaded_model_json)
	# load weights into new model
	loaded_model.load_weights(mypath+'model/'+filename+'.h5')
	print("Loaded model from disk")
	return loaded_model

def lstm_model(name,f):
	c = XGBClassifier(max_depth=100)
	chunk = 10000
	r = 1
	#f = 12
	#f = 7
	#f = 2
	testset = None
	testvalue = None
	
	regressor = Sequential()

	file = Path(mypath+'model/'+name+'_lstm.h5')
	total_history = None
	if file.is_file():
		regressor = load_model(name)
	else:

		regressor.add(LSTM(512, return_sequences=True,
		            input_shape=(f, 1)))  # returns a sequence of vectors of dimension 32
		regressor.add(LSTM(512, return_sequences=True))  # returns a sequence of vectors of dimension 32
		regressor.add(LSTM(512))  # return a single vector of dimension 32
		regressor.add(Dense(1, activation='softmax'))

	regressor.compile(loss='mean_squared_error',
				        optimizer='adam',
				        metrics=['accuracy'])

	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save') 
	#ssc = joblib.load(mypath+'vec/'+name+'_minmaxscaler.save') 

	for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
		df.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
		X_train = ssc.fit_transform(X_train)
		X_train = X_train.reshape(len(X_train),len(df.columns)-1,1)

		print('Chunk '+str(r))
		history = regressor.fit(X_train, Y_train, epochs = 10, batch_size = 32, validation_split=0.1)
		#regressor.reset_states()
		r = r+1
		#if r == 10:
		#	break
		#predict(testset,testvalue,ssc,regressor)
		save_file(pd.DataFrame([[history.history['loss'],history.history['val_loss']]], columns=['loss','val_loss']),
					mypath+'model/'+name+'_history.csv')


		save_lstm_model(regressor,name+'_lstm')
		if Path(mypath+'model/'+name+'_history.csv').is_file():
			total_history = pd.read_csv(mypath+'model/'+name+'_history.csv', index_col=0)
			history_loss(total_history['loss'].values.tolist(), total_history['val_loss'].values.tolist())
		#break

def evaluate_lstm_model(name):
	file = Path(mypath+'model/'+name+'.h5')
	regressor = load_model(name)
	regressor.compile(loss='mean_squared_error',
				        optimizer='adam',
				        metrics=['accuracy'])
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save') 
	chunk = 10000

	for df in  pd.read_csv(mypath+'vec/'+name+'.csv', chunksize=chunk, index_col=0):
		df.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(df, 0.1)
		X_validation = ssc.fit_transform(X_validation)
		X_validation = X_validation.reshape(len(X_validation),len(df.columns)-1,1)
		predict(X_validation,Y_validation,ssc,regressor)


def kmean(n,train,modelname):
	chunk = 30000
	p = Path(mypath+'model/'+modelname+'_kmean_'+str(n)+".pkl" )
	print(modelname)
	if p.is_file():
		print('Model '+modelname+'_kmean_'+str(n)+' already exists')
	else:
		#ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
		kmeans = MiniBatchKMeans(n_clusters=n, random_state=0, batch_size=1000)
		for name in train:
			for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
				df.drop(['txn'], axis=1, inplace=True)
				X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
				#X_train = ssc.transform(X_train)
				kmeans = kmeans.partial_fit(X_train)
				#print('Number of clusters: '+str(len(kmeans.cluster_centers_)))
				#print(kmeans.inertia_)
		save_model(kmeans,modelname+'_kmean_'+str(n))

def eval_kmean(name,test,s,e,c):
	data = []
	for i in range(s,e,c):
		print('Cluster '+str(i))
		modelname = name+'_kmean_'+str(i)
		p = mypath+'model/'+modelname+'.pkl'
		if Path(p).is_file():
			model = pickle.load(open(p, 'rb'))
			df = pd.read_csv(mypath+'/testset/vec/'+test+'.csv', index_col=0).head(500000)
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
			preds = model.predict(X_train)
			from sklearn import metrics
			rs = metrics.adjusted_rand_score(Y_train,preds)
			mis = metrics.adjusted_mutual_info_score(Y_train,preds,average_method='arithmetic')
			fms = metrics.fowlkes_mallows_score(Y_train,preds)
			print('Adjusted Rand index: %0.3f' % rs)
			print('Adjusted Mutual Information score: %0.3f' % mis)
			print('Fowlkes-Mallows score: %0.3f' % fms)
			data.append([i,rs,mis,fms])
		else:
			print('No model: '+modelname+'.pkl')
	df = pd.DataFrame(data,columns=['cluster','adjusted_rand_score','adjusted_mutual_info_score','fowlkes_mallows_score'])
	df.to_csv(mypath+'model/kmean_eval_'+test+'.csv')
	print('save kmean evaluation')

'''
def predict_kmean(name,modelname):
	chunk = 10000
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	if not os.path.exists(mypath+'model_prediction/'):
		os.makedirs(mypath+'model_prediction/')
	#n = [100,1000,5000,10000,15000,20000,25000,30000]
	n = [100,1000,10000]
	for df in  pd.read_csv(mypath+'testset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
		dftest = df.copy()
		dftest.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(dftest, None)
		X_train = ssc.transform(X_train)
		for i in n:
			kmeans = pickle.load(open(mypath+'model/'+modelname+'_kmean_'+str(i)+'.pkl', 'rb'))
			df['kmean_'+str(i)] = kmeans.predict(X_train)[:len(X_train)]
		save_file(df,mypath+'model_prediction/'+name+'_kmean.csv')
		print('save result')
'''
def top(x):
	return x.value_counts().head(10)

def topsum(x):
	return x.sum().head(5)

def get_neighbour(train,modelname):
	chunk = 1000000
	results = []
	model = pickle.load(open(mypath+'model/'+modelname+'.pkl', 'rb'))
	for name in train:
		#ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_testset(df)
			#X_train = ssc.transform(X_train)
			df['cluster'] = model.predict(X_train)[:len(X_train)]
			result = df['icd10'].groupby(df['cluster']).apply(top).to_frame()
			result = result.rename(columns={'icd10':'icd10_count'})
			result.reset_index(inplace=True)
			result = result.rename(columns={'level_1':'icd10'})
			results.append(result)
			#result['kmean_'+str(n)] = result['kmean_'+str(n)].apply(top)
			print('append neighbour to '+modelname)
			#if len(results) == 2:
			#	break
	total = pd.concat(results)
	total = total.groupby(['cluster','icd10']).sum()
	total.reset_index(inplace=True)
	total = total.sort_values(by=['cluster','icd10_count'], ascending=[True,False])
	total = total.groupby(['cluster']).head(10)
	total.to_csv(mypath+'/model_prediction/'+modelname+'_neighbour.csv')

def get_weight(modelname):
	df = pd.read_csv(mypath+'model_prediction/'+modelname+'_neighbour.csv', index_col=0)
	df['total_count'] = df.groupby('icd10')['icd10_count'].transform('sum')
	df['cluster_count'] = df.groupby('cluster')['icd10_count'].transform('sum')
	df['weight'] = df['icd10_count']/(df['total_count']*df['cluster_count'])
	df = df.sort_values(by=['cluster','weight'], ascending=[True,False])
	df.to_csv(mypath+'model_prediction/'+modelname+'_neighbour.csv')
	print('save weight to '+modelname)

def remove_all_temp_weight(modelname,n):
	for i in range(n):
		remove_file(mypath+'model_prediction/'+modelname+'_'+str(n)+'_'+str(i)+'.csv')

def agg_weight(df1,df2):
	df2 = df2[['icd10','icd10_count']]
	df = df1.append(df2)
	result = df.groupby('icd10')['icd10_count'].agg('sum').to_frame()
	result = result.sort_values(by=['icd10'], ascending=[True])
	result = result.reset_index()
	return result

def save_weight(modelname,df,n,x):
	p = mypath+'model_prediction/'+modelname+'_'+str(n)+'_'+str(x)+'.csv'
	file = Path(p)
	if file.is_file():
		d = pd.read_csv(p, index_col=0)
		result = agg_weight(d,df)
		result.to_csv(p)
	else:
		data = []
		for i in range(38970):
			data.append([i,0])
		d = pd.DataFrame(data,columns=['icd10','icd10_count'])
		result = agg_weight(d,df)
		result.to_csv(p)
def get_total_icd10_weight(n,modelname):
	dfs = []
	for i in range(n):
		p = mypath+'model_prediction/'+modelname+'_'+str(n)+'_'+str(i)+'.csv'
		df = pd.read_csv(p, index_col=0)
		dfs.append(df)
	df = pd.concat(dfs)
	df['total_icd10_count'] = df.groupby(['icd10'])['icd10_count'].transform('sum')
	df.drop(['icd10_count'], axis=1, inplace=True)
	df = df.drop_duplicates()
	return df
	print(df)
	for i in range(n):
		p = mypath+'model_prediction/'+modelname+'_'+str(n)+'_'+str(i)+'.csv'
		d = pd.read_csv(p, index_col=0)
		result = pd.merge(d,df, how='inner', on='icd10')
		result = result.drop_duplicates()
		print(result)
	return df

def get_total_weight(n,train,modelname,inplace=True):

	num = 0
	chunk = 1000
	model = pickle.load(open(mypath+'model/'+modelname+'_kmean_'+str(n)+'.pkl', 'rb'))
	start = True
	if inplace:
		remove_all_temp_weight(modelname,n)
	else:
		log = Path(mypath+'log/'+modelname+'.txt')
		if log.is_file():
			start = False
	for name in train:
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			if start:
				df.drop(['txn'], axis=1, inplace=True)
				X_train, X_validation, Y_train, Y_validation = get_testset(df)
				df['cluster'] = model.predict(X_train)[:len(X_train)]
				result = df.groupby(['cluster','icd10']).size().reset_index(name='icd10_count')
				#result = df['icd10'].groupby(df['cluster']).apply(top).to_frame()
				#result = result.rename(columns={'icd10':'icd10_count'})
				#result.reset_index(inplace=True)
				#result = result.rename(columns={'level_1':'icd10'})
				#print(result)
				for i in range(n):
					save_weight(modelname,result[result['cluster']==i],n,i)
				num = num + chunk
				print('append total weight to '+modelname+': '+name+'_'+str(num))
				f = open(mypath+'log/'+modelname+'.txt','w+')
				f.write(name+'_'+str(num))
				f.close()
			else:
				f = open(mypath+'log/'+modelname+'.txt','r')
				s = f.read()
				num = num + chunk
				print('skip '+name+'_'+str(num))
				if s == name+'_'+str(num):
					start = True

	total = get_total_icd10_weight(n,modelname)
	for i in range(n):
		p = mypath+'model_prediction/'+modelname+'_'+str(n)+'_'+str(i)+'.csv'
		df = pd.read_csv(p, index_col=0)
		df['icd10_inner_weight'] =  df['icd10_count']/df['icd10_count'].sum()
		result = pd.merge(df,total, how='inner', on='icd10')
		result['icd10_weight'] = result['icd10_inner_weight']/result['total_icd10_count']
		result = result.fillna(0)
		print(result)
		result.to_csv(p)
		print('saved icd10 weight '+str(i))
	print('saved weight')

def cluster_validate(n,train,modelname):
	chunk = 5000
	model = pickle.load(open(mypath+'model/'+modelname+'_kmean_'+str(n)+'.pkl', 'rb'))
	print('n_cluster = '+str(n))
	print('model name = '+modelname)
	for name in train:
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			txn = df['txn']
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_testset(df)
			df['cluster'] = model.predict(X_train)[:len(X_train)]
			df['txn'] = txn
			df = df.rename(columns={'icd10':'actual_icd10'})
			df['n'] = n
			df['modelname'] = modelname
			#print(df)
			cluster_performance(df)
			break
		break
def predict_cluster(train,modelname):
	chunk = 100000
	model = pickle.load(open(mypath+'model/'+modelname+'.pkl', 'rb'))
	neighbour = pd.read_csv(mypath+'model_prediction/'+modelname+'_neighbour.csv', index_col=0)
	neighbour = neighbour.rename(columns={'icd10':'predicted_icd10'})
	for name in train:
		remove_file(mypath+'result/'+name+'_'+modelname+'.csv')
		for df in pd.read_csv(mypath+'testset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			txn = df['txn']
			df.drop(['txn'], axis=1, inplace=True)
			index = df.index
			X_train, X_validation, Y_train, Y_validation = get_testset(df)
			#X_train = ssc.transform(X_train)
			df.insert(0,'index',index)
			df['txn'] = txn
			df['model_name'] = modelname
			df['cluster'] = model.predict(X_train)[:len(X_train)]
			result = pd.merge(df,neighbour, how='left', on='cluster')
			#print(result)
			save_file(result,mypath+'result/'+name+'_'+modelname+'.csv')
			print('append predicted cluster to '+modelname)
			#print(df)
	print('complete')
def combine_prediction(files,modelname):
	chunk = 100000
	remove_file(mypath+'result/combined_'+modelname+'.csv')
	for name in files:
		for df in pd.read_csv(mypath+'result/'+name+'.csv', chunksize=chunk, index_col=0):
			#print(df)
			df = df[['index','icd10','predicted_icd10','weight']]
			save_file(df,mypath+'result/combined_'+modelname+'.csv')
			print('append combine_prediction')
	print('Saved combined_'+modelname)

def test_icd10_prediction(name,modelname):
	preds = pd.read_csv(mypath+'result/'+name+'_'+modelname+'_prediction.csv', index_col=0)
	testset = preds.copy()
	result = None
	remove_file(mypath+'result/'+name+'_'+modelname+'_prediction_onehot.csv')
	for i in range(10):
		if i == 0:
			result = preds.groupby('txn').nth(i)
			result = result.rename(columns={'predicted_icd10':'predicted_icd10_0','sum_weight':'sum_weight_0'})
		else:
			result['predicted_icd10_'+str(i)] = preds.groupby('txn').nth(i)['predicted_icd10']
			result['sum_weight_'+str(i)] = preds.groupby('txn').nth(i)['sum_weight']
	result = result.reset_index()
	result.to_csv(mypath+'result/'+name+'_'+modelname+'_prediction_onehot.csv')

def predict_icd10(train,modelname):
	chunk = 100000
	for name in train:
		print(name)
		remove_file(mypath+'result/'+name+'_'+modelname+'_prediction.csv')
		txns = []
		for df in pd.read_csv(mypath+'testset/vec/'+name+'.csv', chunksize=100000, index_col=0):
			txns.append(df['txn'])

		id = pd.concat(txns)
		id = id.drop_duplicates()
		id = id.tolist()

		for i in range(0, len(id), chunk):
			index = id[i:i + chunk]
			result = []
			for df in pd.read_csv(mypath+'result/'+name+'_'+modelname+'.csv', chunksize=chunk, index_col=0):
				df = df[df['txn'].isin(index)]
				result.append(df)
			total = pd.concat(result)
			print(total)
			total = total[['txn','predicted_icd10','weight']]
			#total = total.groupby(['txn', 'predicted_icd10'])['weight'].agg('sum')
			total['sum_weight'] = total.groupby(['txn','predicted_icd10'])['weight'].transform('sum')
			total = total[['txn','predicted_icd10','sum_weight']]
			total = total.drop_duplicates()
			total = total.sort_values(by=['txn','sum_weight'], ascending=[True,False])
			print(total)
			save_file(total,mypath+'result/'+name+'_'+modelname+'_prediction.csv')
			print('append predicted_icd10 prediction')
			#break
		
	print('complete')

def bag_validate(train,modelname,combine=False):

	chunk = 10000
	n = 10
	for name in train:
		txn = []
		for df in pd.read_csv(mypath+'testset/raw/'+name+'.csv', chunksize=100000, index_col=0):
			txn = txn + df['txn'].values.tolist()

		for i in range(0, len(txn), chunk):
			txn_range = txn[i:i + chunk]
			test = []
			for df in pd.read_csv(mypath+'testset/raw/'+name+'.csv', chunksize=100000, index_col=0):
				df = df[df['txn'].isin(txn_range)]
				df = df[['txn','icd10']]
				test.append(df)
			testset = pd.concat(test)
			testset = testset.drop_duplicates()
			result = []
			filename = name+'_'+modelname
			if combine:
				filename = modelname
			for df in pd.read_csv(mypath+'result/'+filename+'.csv', chunksize=chunk, index_col=0):
				df = df[df['txn'].isin(testset.txn.values.tolist())]
				result.append(df)
			predictset = pd.concat(result)
			predictset = predictset[['txn','icd10','predicted_icd10','weight']]
			predictset = predictset.rename(columns={'icd10':'actual_icd10'})
			print(testset)
			print(predictset)
			total = pd.merge(testset, predictset, on=['txn'])
			#total.drop(['drug_y','drug_name_y'], axis=1, inplace=True)
			#total = total.rename(columns={'drug_x':'drug','drug_name_x':'drug_name','icd10_x':'icd10','icd10_y':'actual_icd10'})
			#print(total)
			validateset = total[['txn','predicted_icd10','weight']]
			validateset['sum_weight'] = validateset.groupby(['txn','predicted_icd10'])['weight'].transform('sum')
			validateset = validateset.sort_values(by=['txn','sum_weight'], ascending=[True,False])
			validateset.drop(['weight'], axis=1, inplace=True)
			validateset = validateset.drop_duplicates()
			validateset = validateset.groupby('txn').head(n)

			actualset = total[['txn','actual_icd10']]
			actualset = actualset.drop_duplicates()

			dataset1 = pd.merge(validateset, actualset, how='left', left_on=['txn','predicted_icd10'], right_on=['txn','actual_icd10'])
			dataset2 = pd.merge(actualset, validateset, how='left', right_on=['txn','predicted_icd10'], left_on=['txn','actual_icd10'])
			dataset = dataset1.append(dataset2, ignore_index=True)
			dataset = dataset.drop_duplicates()
			dataset = dataset.sort_values(by=['txn','sum_weight'], ascending=[True,False])
			print(dataset)
			dataset.to_csv('test.csv')
			bag_performance(dataset.head(1000))
			break
			#print('append prediction')
		break
	print('complete')

	#performance(None)

def count(x):
	return len(x[x['actual_icd10'].isna()]) + len(x[(pd.notna(x['actual_icd10'])) & (pd.notna(x['predicted_icd10']))])

def dxn(x):
	return len(x[pd.notna(x['actual_icd10'])])

def true_positive(x):
	return len(x[(pd.notna(x['actual_icd10'])) & (pd.notna(x['predicted_icd10']))])

def false_positive(x):
	df = x.reset_index()
	total = len(df)
	actual = len(df[(pd.notna(df['actual_icd10']))])
	df = df[(pd.notna(df['actual_icd10'])) & (pd.notna(df['predicted_icd10']))]
	if len(df) == 0:
		return total - actual
	else:
		return df.tail(1).index.values.astype(int)[0]-len(df)+1

def true_negative(x):
	df = x.reset_index()
	df1 = df[(pd.notna(df['actual_icd10'])) & (pd.notna(df['predicted_icd10']))]
	if len(df1) == 0:
		return 0
	else:
		return len(df[(df['actual_icd10'].isna()) & (df['predicted_icd10'].index > df1.tail(1).index.values.astype(int)[0])])

def false_negative(x):
	return len(x[(pd.notna(x['actual_icd10'])) & (x['predicted_icd10'].isna())])

def rank_y_true(x):
	y_true = [0] * 38970

	for i in x['actual_icd10'].values.tolist():
		if pd.notna(i):
			y_true[int(i)] = 1
	
	return y_true

def rank_y_score(x):
	y_score = [0] * 38970
	
	for i in range(len(x['predicted_icd10'].values.tolist())):
		v = x['predicted_icd10'].values.tolist()[i]
		if pd.notna(v):
			y_score[int(v)] = x['sum_weight'].values.tolist()[i]
	return y_score

def rank_total_y_score(x):
	p = mypath+'model_prediction/'+x['modelname'].iloc[0]+'_'+str(x['n'].iloc[0])+'_'+str(x['cluster'].iloc[0])+'.csv'
	df = pd.read_csv(p, index_col=0)
	return df['icd10_weight'].values.tolist()

def cluster_performance(df):
	#print(df)
	#df = pd.read_csv('test.csv', index_col=0)
	#df = df.head(500)
	'''
	result = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(count).reset_index(name='n')
	result['dxn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(dxn).reset_index(name='dxn')['dxn']
	result['tp'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(tp).reset_index(name='tp')['tp']
	result['fp'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(fp).reset_index(name='fp')['fp']
	result['tn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(tn).reset_index(name='tn')['tn']
	result['fn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(fn).reset_index(name='fn')['fn']
	result['accuracy'] = (result['tp']+result['tn'])/result['n']
	result['precision'] = result['tp']/(result['tp']+result['fp'])
	result['recall'] = result['tp']/(result['tp']+result['fn'])
	result['f_measure'] = 2*result['tp']/((2*result['tp'])+result['fp']+result['fn'])

	#print(result)
	print((result['accuracy']*result['dxn']).sum()/result['dxn'].sum())
	print((result['precision']*result['dxn']).sum()/result['dxn'].sum())
	print((result['recall']*result['dxn']).sum()/result['dxn'].sum())
	print((result['f_measure']*result['dxn']).sum()/result['dxn'].sum())
	'''
	y_true = np.array(df.groupby('txn').apply(rank_y_true).reset_index(name='y_true')['y_true'].values.tolist())
	#y_score = np.array(df.groupby('txn').apply(rank_y_score).reset_index(name='y_score')['y_score'].values.tolist())
	y_score = np.array(df.groupby('txn').apply(rank_total_y_score).reset_index(name='y_score')['y_score'].values.tolist())
	'''
	l = 10
	for i in range(len(y_true)):
		d = pd.DataFrame([y_true[i],y_score[i]]).T
		d.rename(columns={0:'actual_icd10',1:'predicted_icd10'},inplace=True)
		d = d.sort_values(by=['predicted_icd10'], ascending=[False])
		n = len(d[d['actual_icd10']==1])
		#print('total actual icd10: '+str(n))
		print(d[d['actual_icd10']==1])
		d = d.head(l)
		print(d)
		d.reset_index(drop=True,inplace=True)
		d['index'] = d.index
		tp = len(d[d['actual_icd10']==1])
		fp = l
		tn = 0
		if len(d[d['actual_icd10']==1]) > 0:
			lastp = d[d['actual_icd10']==1].tail(1).index.values.astype(int)[0]
			fp = len(d[(d['actual_icd10']==0)&(d['index']<lastp)])
			tn = len(d[d['index'] > lastp])
		fn = n-tp
		#print('TP = '+str(tp))
		#print('FP = '+str(fp))
		#print('TN = '+str(tn))
		#print('FN = '+str(fn))
		print('Accuracy = '+str((tp+tn)/l))
		print('Precision = '+str(tp/(tp+fp)))
		print('Recall = '+str(tp/(tp+fn)))
		print('F1-measure = '+str(2*tp/((2*tp)+fp+fn)))
	'''

	print('coverage error '+ str(coverage_error(y_true, y_score)))
	print('Average precision score '+ str(label_ranking_average_precision_score(y_true, y_score)))
	print('Ranking loss '+ str(label_ranking_loss(y_true, y_score)))

def bag_performance(df):
	#print(df)
	#df = pd.read_csv('test.csv', index_col=0)
	#df = df.head(1000)

	result = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(count).reset_index(name='n')
	result['dxn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(dxn).reset_index(name='dxn')['dxn']
	result['tp'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(true_positive).reset_index(name='tp')['tp']
	result['fp'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(false_positive).reset_index(name='fp')['fp']
	result['tn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(true_negative).reset_index(name='tn')['tn']
	result['fn'] = df.groupby('txn')['actual_icd10','predicted_icd10'].apply(false_negative).reset_index(name='fn')['fn']
	result['accuracy'] = (result['tp']+result['tn'])/result['n']
	result['precision'] = result['tp']/(result['tp']+result['fp'])
	result['recall'] = result['tp']/(result['tp']+result['fn'])
	result['f_measure'] = 2*result['tp']/((2*result['tp'])+result['fp']+result['fn'])

	#print(result)
	print((result['accuracy']*result['dxn']).sum()/result['dxn'].sum())
	print((result['precision']*result['dxn']).sum()/result['dxn'].sum())
	print((result['recall']*result['dxn']).sum()/result['dxn'].sum())
	print((result['f_measure']*result['dxn']).sum()/result['dxn'].sum())

	y_true = np.array(df.groupby('txn').apply(rank_y_true).reset_index(name='y_true')['y_true'].values.tolist())
	y_score = np.array(df.groupby('txn').apply(rank_y_score).reset_index(name='y_score')['y_score'].values.tolist())

	l = 10
	for i in range(len(y_true)):
		d = pd.DataFrame([y_true[i],y_score[i]]).T
		d.rename(columns={0:'actual_icd10',1:'predicted_icd10'},inplace=True)
		d = d.sort_values(by=['predicted_icd10'], ascending=[False])
		n = len(d[d['actual_icd10']==1])
		#print('total actual icd10: '+str(n))
		print(d[d['actual_icd10']==1])
		d = d.head(l)
		print(d)
		d.reset_index(drop=True,inplace=True)
		d['index'] = d.index
		tp = len(d[d['actual_icd10']==1])
		fp = l
		tn = 0
		if len(d[d['actual_icd10']==1]) > 0:
			lastp = d[d['actual_icd10']==1].tail(1).index.values.astype(int)[0]
			fp = len(d[(d['actual_icd10']==0)&(d['index']<lastp)])
			tn = len(d[d['index'] > lastp])
		fn = n-tp
		print('TP = '+str(tp))
		print('FP = '+str(fp))
		print('TN = '+str(tn))
		print('FN = '+str(fn))
		print('Accuracy = '+str((tp+tn)/l))
		print('Precision = '+str(tp/(tp+fp)))
		print('Recall = '+str(tp/(tp+fn)))
		print('F1-measure = '+str(2*tp/((2*tp)+fp+fn)))

def distance(x,t):
	return x
def birch_finetune(train,t):
	chunk = 20000
	gap = t/2
	print(train)
	while True:
		b = Birch(n_clusters=None,threshold=t)
		n = 1
		print('Threshold :'+str(t))
		for name in train:
			for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
				df.drop(['txn'], axis=1, inplace=True)
				#if name == 'reg':
				#	df.insert(9,'room_dc',0)
				X_train, X_validation, Y_train, Y_validation = get_testset(df)
				b = b.partial_fit(X_train)
				n = len(b.subcluster_centers_)
				print('Threshold :'+str(t))
				print('Number of cluster :'+str(n))
				if n > 15000:
					break
			if n > 15000:
				break
		gap = gap/2
		if n > 15000:
			t = t+gap
		else:
			t = t-gap
		print('Number of cluster :'+str(n))
		#print('Adjust threshold to :'+str(t))
		if gap < 0.01:
			#print('Target threshold for '+str(train)+' : '+str(t))
			break

		#plt.figure(figsize=(8, 6))
		#plt.scatter(X_train[:,0], X_train[:,1], c=b.labels_.astype(float))
		#plt.show()

def kmean_finetune(name):

	chunk = 100000
	t = 0.1
	data = None
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
		data = df
		break
	data.drop(['txn'], axis=1, inplace=True)
	X_train, X_validation, Y_train, Y_validation = get_testset(data)
	X_train = ssc.transform(X_train)
	ss = []
	r = range(10,15)
	for k in r:
		kmeans = MiniBatchKMeans(n_clusters=k, random_state=0, batch_size=1000)
		kmeans = kmeans.fit(X_train)
		ss.append(kmeans.inertia_)
		# Getting the cluster labels
		labels = kmeans.predict(X_train)
		# Centroid values
		centroids = kmeans.cluster_centers_
		plt.figure(figsize=(8, 6))
		plt.scatter(X_train[:,0], X_train[:,1], c=kmeans.labels_.astype(float))
		plt.show()
	'''
	plt.plot(r, ss, 'bx-')
	plt.xlabel('k')
	plt.ylabel('Sum_of_squared_distances')
	plt.title('Elbow Method For Optimal k')
	plt.show()
	'''

	'''
	df1 = pd.concat(samples)
	X_train, X_validation, Y_train, Y_validation = get_testset(df1)
	
	for i in range(1,100,1):
		i = i*100
		b = Birch(n_clusters=i,threshold=0.01)
		b = b.fit(X_train)
		df = df1.copy()
		df['cluster'] = b.predict(X_train)[:len(X_train)]
		df['icd10_count'] = df.groupby(['cluster','icd10'])['icd10'].transform('count')
		df['icd10_totalcount'] = df.groupby('cluster')['icd10'].transform('count')
		df['ratio'] = df['icd10_count']/df['icd10_totalcount']
		df = df.sort_values(by=['cluster','icd10_count'], ascending=[True,False])
		df = df[['icd10','cluster','ratio']]
		df = df.drop_duplicates()
		print('Threshold '+str(i)+' '+str(df['ratio'].mean()))
	'''
	'''
		t = b.transform(X_train)[:len(X_train)]
		df['distances'] = t.tolist()
		df['distance'] = df.apply(lambda row: row['distances'][row['cluster']], axis=1)
		df['distance'] = df['distance']*df['distance']
		df['square'] = df.groupby('cluster')['distance'].transform('sum')
		df = df[['cluster','square']]
		df = df.drop_duplicates()
		df = df.fillna(0)
		s = df['square'].sum()
		print(str(i)+','+str(len(b.subcluster_centers_))+','+str(s))
		#break
	'''
'''
def birch_train(train,modelname):
	chunk = 100000
	mypath = mypath+''
	#mypath = '/media/bon/My Passport/data/'
	n = 0
	t = 0.5
	target_cluster = 5000
	while True:
		n = 0
		print('Threshold = '+str(t))
		b = Birch(n_clusters=None,threshold=t)
		for name in train:
			#ssc = jl.load(mypath+'vec/'+name+'_standardscaler.save')

			for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
				df.drop(['txn'], axis=1, inplace=True)
				if name == 'reg':
					df.insert(9,'room_dc',0)
				X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
				#X_train = ssc.transform(X_train)
				b = b.partial_fit(X_train)
				n = len(b.subcluster_centers_)
				print('Number of cluster: '+modelname+' '+str(n))
				if n > target_cluster:
					print('Too many clusters')
					break
			if n > target_cluster:
				break
		if n <= target_cluster:
			save_model(b,modelname+'_'+str(t))
			print('save birch model')
			break
		else:
			t = t+0.1
	print('complete')
'''
def birch_train(train,modelname,t):
	chunk = 10000
	print('Threshold = '+str(t))
	b = Birch(n_clusters=None,threshold=t)
	for name in train:
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			df.drop(['txn'], axis=1, inplace=True)
			#if name == 'reg':
			#	df.insert(9,'room_dc',0)
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
			b = b.partial_fit(X_train)
			n = len(b.subcluster_centers_)
			print('Number of cluster: '+modelname+' '+str(n))

	save_model(b,modelname)
	print('complete')

def train_had():
	icd10 =  pd.read_csv(mypath+'raw/icd10.csv', index_col=0)
	icd10_map = dict(zip(icd10['code'],icd10.index))
	had = pd.read_csv(mypath+'had.csv', index_col=0)
	had = had['drug'].values.tolist()
	chunk = 50000
	n = 0
	#m = Incremental(MLPClassifier())
	for name in ['dru','idru']:
		m = Incremental(MLPClassifier())
		#m = Incremental(BernoulliNB())
		for df in  pd.read_csv(mypath+'trainingset/raw/'+name+'.csv', chunksize=chunk, index_col=0, low_memory=False):	
			df = df[['icd10','dx_type','drug']]
			df = pd.concat([df.drop('icd10', axis=1), df['icd10'].map(icd10_map)], axis=1)
			df['had'] = np.where(df['drug'].isin(had), 1, 0)
			df = df[['icd10','dx_type','had']]
			df1 = df[df['had'] == 1]
			df1 = df1.drop_duplicates()
			df2 = df[~df['icd10'].isin(df1['icd10'].values.tolist())]
			df2 = df2.drop_duplicates()
			df = pd.concat([df1,df2])
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
			m.partial_fit(X_train, Y_train, classes=[0,1])
			n = n + chunk
			print('fit '+str(n))
			#print('Loss :'+str(m.loss_))

		save_model(m,name+'_had_mlpclassifier')
		#save_model(m,name+'_had_nb')
	#save_model(m,'drug_had_mlpclassifier')

def eval_had(name):
	chunk = 1000000
	#loaded_model = pickle.load(open(mypath+'model/'+name+'_had_mlpclassifier.pkl', 'rb'))
	#loaded_model = pickle.load(open(mypath+'model/'+name+'_had_nb.pkl', 'rb'))
	loaded_model = pickle.load(open(mypath+'model/drug_had_mlpclassifier.pkl', 'rb'))
	icd10 =  pd.read_csv(mypath+'raw/icd10.csv', index_col=0)
	icd10_map = dict(zip(icd10['code'],icd10.index))
	had = pd.read_csv(mypath+'had.csv', index_col=0)
	had = had['drug'].values.tolist()

	for df in pd.read_csv(mypath+'testset/raw/'+name+'.csv', chunksize=chunk, index_col=0):
		dftest = df.copy()
		dftest = pd.concat([dftest.drop('icd10', axis=1), dftest['icd10'].map(icd10_map)], axis=1)
		
		dftest['had'] = np.where(dftest['drug'].isin(had), 1, 0)
		dftest = dftest[['icd10','dx_type','had']]
		df1 = dftest[dftest['had'] == 1]
		df1 = df1.drop_duplicates()
		df2 = dftest[~dftest['icd10'].isin(df1['icd10'].values.tolist())]
		df2 = df2.drop_duplicates()
		dftest = pd.concat([df1,df2])
		'''
		no_had = dftest[dftest['had']==0]
		yes_had = dftest[dftest['had']==1]
		if len(no_had) > len(yes_had):
			no_had = resample(no_had,
                                replace = False, # sample without replacement
                                n_samples = len(yes_had), # match minority n
                                random_state = 27) # reproducible results
		else:
			yes_had = resample(yes_had,
                                replace = False, # sample without replacement
                                n_samples = len(no_had), # match minority n
                                random_state = 27) # reproducible results
		dftest = pd.concat([no_had,yes_had])
		'''
		X_train, X_validation, Y_train, Y_validation = get_testset(dftest)
		y_pred = loaded_model.predict(X_train)
		cf = confusion_matrix(Y_train, y_pred)
		print(cf)
		cr = classification_report(Y_train, y_pred)
		print(cr)
		
		dftest = df.copy()
		dftest = pd.concat([dftest.drop('icd10', axis=1), dftest['icd10'].map(icd10_map)], axis=1)
		dftest = dftest[['icd10','dx_type','drug']]
		X_train, X_validation, Y_train, Y_validation = get_testset(dftest)
		p = loaded_model.predict_proba(X_train)
		dfp = pd.DataFrame(data=p,columns=['no_had','yes_had'])
		df['no_had'] = dfp['no_had'].values.tolist()
		df['yes_had'] = dfp['yes_had'].values.tolist()
		#print(df)
		print('Predict '+name)
		df = df.head(10000)
		df.to_csv(mypath+'model_prediction/'+name+'_had.csv')
		
		break

def cosine_vectorized(array1, array2):
    sumyy = (array2**2).sum(1)
    sumxx = (array1**2).sum(1, keepdims=1)
    sumxy = array1.dot(array2.T)
    return (sumxy/np.sqrt(sumxx))/np.sqrt(sumyy)

def train_lgb(train):
	chunk = 100000
	lgb_estimator = None
	# First one necessary for incremental learning:
	lgb_params = {
	  'objective': 'regression',
	  'verbosity': 100
	}
	evals_result = {}
	for name in train:
		for df in pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, 0.1)
			lgb_estimator = lgb.train(lgb_params,
                         # Pass partially trained model:
                         init_model=lgb_estimator,
                         train_set=lgb.Dataset(X_train, Y_train),
                         valid_sets=lgb.Dataset(X_validation, Y_validation),
								 evals_result=evals_result,
                         num_boost_round=100,
								 keep_training_booster=True)
			Y_pred = list(lgb_estimator.predict(X_validation))
			y_pred = [round(x) for x in Y_pred]
			#print(list(Y_validation))
			#print(y_pred)
			acc = accuracy_score(list(Y_validation), y_pred)
			print(acc)
			sim = cosine_similarity([list(Y_validation)], [y_pred])
			print(sim)
			del df, X_train, X_validation, Y_train, Y_validation
			gc.collect()
			#print(evals_result)

def train_xgb(train):
	chunk = 1000
	xgb_estimator = None
	# First three are for incremental learning:
	xgb_params = {
	  'updater':'refresh',
	  'process_type': 'update',
	  'refresh_leaf': True,
	  'silent': False,
	  }
	for name in train:
		for df in pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			df.drop(['txn'], axis=1, inplace=True)
			X_train, X_validation, Y_train, Y_validation = get_dataset(df, 0.1)

			xgb_estimator = xgb.train({}, 
                        dtrain=xgb.DMatrix(X_train, label=Y_train),
                        evals=[(xgb.DMatrix(X_validation, Y_validation),"Valid")],
                        num_boost_round=100,
                        xgb_model = xgb_estimator)
		
			Y_pred = list(xgb_estimator.predict(xgb.DMatrix(X_validation)))
			y_pred = [round(x) for x in Y_pred]
			acc = accuracy_score(list(Y_validation), y_pred)
			print(acc)
			sim = cosine_similarity([list(Y_validation)], [y_pred])
			print(sim)
			del df, X_train, X_validation, Y_train, Y_validation
			gc.collect()


def apply_pca(name):
	chunk = 1000000
	print(name)
	ssc = joblib.load(mypath+'vec/'+name+'_standardscaler.save')
	for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
		df.drop(['txn'], axis=1, inplace=True)
		X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
		X_train = ssc.transform(X_train)
		kmeans = MiniBatchKMeans(n_clusters=10, random_state=0, batch_size=1000)
		kmeans = kmeans.partial_fit(X_train)
		print('Before PCA')
		print(kmeans.inertia_)

		#keep 95% variance
		pca = PCA(n_components=0.80)
		#guess the best dimension
		#pca = PCA(n_components='mle')
		pca.fit(X_train)
		#print(pca.n_components_)
		X_train = pca.transform(X_train)
		kmeans = MiniBatchKMeans(n_clusters=10, random_state=0, batch_size=1000)
		kmeans = kmeans.partial_fit(X_train)
		print('After PCA')
		print(kmeans.inertia_)

def get_random_dataset(name,n):
	d = []
	chunk = 1000000
	icd10 = pd.read_csv(mypath+'raw/icd10.csv', index_col=0)
	icd10_dict = dict(zip(icd10.index,icd10.code))
	while True:
		for df in  pd.read_csv(mypath+'trainingset/vec/'+name+'.csv', chunksize=chunk, index_col=0):
			d.append(df.sample(n=1000))
			result = pd.concat(d)
			result = result.drop_duplicates()
			#print(result.groupby('icd10').count().sort_values(by=['txn'], ascending=[False]))
			#top_dx = result.groupby('icd10').count().sort_values(by=['txn'], ascending=[False]).reset_index()
			#print(top_dx['icd10'].head(10))
			#result = result[result['icd10'].isin(top_dx['icd10'].head(10))]
			print(result)
			if len(result) >= n:
				result['icd10'] = result['icd10'].apply(lambda x: icd10_dict[x] if x in icd10_dict else 'no_icd10')
				return result

def train_gb(df,name,i):
	df.drop(['txn'], axis=1, inplace=True)
	X_train, X_validation, Y_train, Y_validation = get_dataset(df, None)
	clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=10, random_state=0)
	clf.fit(X_train,Y_train)
	pkl_filename = mypath+'gb_model_random/'+name+'_gb_'+str(i)+'.pkl'
	with open(pkl_filename, 'wb') as file:
		 pickle.dump(clf, file)
	print("save model")
	#scores = cross_val_score(clf, X_train, Y_train, cv=3)
	#print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))


def create_gradientboosting_group(name):
	for i in range(10):
		print(i)
		df = get_random_dataset('dru',10000)
		print(df)
		train_gb(df,name,i)
