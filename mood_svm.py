import sys
import os
sys.path.append('/home/will/Documents/data/lib/libsvm-3.17/python')
from svmutil import *



def train(model_file,train_data,scale_model):
	cmd = './svm-scale -s %s %s > %s'%(scale_model,train_data,'train_scaled_data')
	os.system(cmd)
	y,x = svm_read_problem('train_scaled_data')
	model = svm_train(y,x)
	svm_save_model(model_file , model)

def classify(scale_model,model_file,predict_data,evaluate=False):
	m = svm_load_model(model_file)
	cmd = './svm-scale -r %s %s > %s'%(scale_model,predict_data,'predict_scaled_data')
	os.system(cmd)

	y,x = svm_read_problem('predict_scaled_data')
	p_labels,p_acc,p_vals = svm_predict(y,x,m)
	if evaluate == True:
		(acc,mse,scc) = evaluations(y,p_labels)
		print acc,mse,scc
	else:
		return p_labels 

def train_and_classify(scale_model,model_file,train_data,predict_data):
	cmd = './svm-scale -s %s %s > %s'%(scale_model,train_data,'train_scaled_data')
	os.system(cmd)
	cmd = './svm-scale -r %s %s > %s'%(scale_model,predict_data,'predict_scaled_data')
	os.system(cmd)
	train.train('train_scaled_data',model_file)
	classify.classify(model_file,'predict_scaled_data')

