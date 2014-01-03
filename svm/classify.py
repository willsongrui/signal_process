import sys
sys.path.append('/home/will/Documents/data/lib/libsvm-3.17/python')
from svmutil import *

def classify(model_file,input_file):
	m = svm_load_model(model_file)
	y,x = svm_read_problem(input_file)
	p_labels,p_acc,p_vals = svm_predict(y,x,m)
	(acc,mse,scc) = evaluations(y,p_labels)
	print acc,mse,scc
if __name__=='__main__':
	if len(sys.argv)<3:
		sys.exit
	m = sys.argv[1]
	i = sys.argv[2]
	classify(model_file=m,input_file=i)