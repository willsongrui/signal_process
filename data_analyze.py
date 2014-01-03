import sys
import os
import numpy as np
result = [[0,0,0,0,0,0],[0,0,0,0,0,0]]
fs = open(sys.argv[1],'r')
count = [0,0]
for line in fs.readlines():
	data = line.split(' ')
	#print data
	cur = []
	for i in range(1,6):
		result[int(data[0])][i-1] = result[int(data[0])][i-1] + float(data[i][2:]) 
	result[int(data[0])][5] = result[int(data[0])][5] + float(data[6][2:-2])
	count[int(data[0])] = count[int(data[0])]+1 	
	
print 'neutral:'
for i in range(6):
	print result[0][i]*1.0/count[0]
print 'angry'
for i in range(6):
	print result[1][i]*1.0/count[1]