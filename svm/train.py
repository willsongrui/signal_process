import sys
sys.path.append('/home/will/Documents/data/lib/libsvm-3.17/python')
from svmutil import *
def train(data_file,model_file):
	y,x = svm_read_problem(data_file)
	model = svm_train(y,x)
	svm_save_model(model_file , model)
if __name__ == '__main__':
	if len(sys.argv)<3:
		sys.exit()
	data_file = sys.argv[1]
	model_file = sys.argv[2]
	train(data_file,model_file)
	
