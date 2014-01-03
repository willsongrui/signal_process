import sys
import os
sys.path.append('/home/will/Documents/data/lib/libsvm-3.17/python')
from svmutil import *
import train
import classify
if __name__ == '__main__':
	if len(sys.argv)<3:
		sys.exit()
	train_data = sys.argv[1]
	predict_data = sys.argv[2]

	
	cmd = './svm-scale -s %s %s > %s'%('model_file',train_data,'train_scaled_data')
	os.system(cmd)
	cmd = './svm-scale -r %s %s > %s'%('model_file',predict_data,'predict_scaled_data')
	os.system(cmd)
	train.train('train_scaled_data','model_file')
	classify.classify('model_file','predict_scaled_data')
