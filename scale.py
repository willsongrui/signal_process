def scale(file_name,out):
	feature_num = 0
	feature_max = [0]
	feature_min = [0]
	records = []
	try:
		fs = open(file_name,'r')

	except:
		print 'Input File cannot be found'
		sys.exit()
	for line in fs.read_lines:
		
		features = line.split(' ')
		if features[0] not in ['-1','0','1']:
			print 'wrong labels'
			sys.exit()
		cnt = 1
		record = [features[0]]
		for index,feature in enumerate(features[1:]):
			loc = feature.find(':')
			if cnt!=int(feature[:loc]):
				print 'wrong feature index %d'%(index)
				sys.exit()
			amount = float(feature[loc+1:])
			record.append(amount)
			if feature_num<cnt:
				feature_min.append(amount)
				feature_max.append(amount)
				feature_num = feature_num+1
			else:
				feature_max[cnt] = max(feature_max[cnt],amount)
				feature_min[cnt] = min(feature_min[cnt],amount)
		records.append(record)
	fs.close()
	try:
		fs = open(out,'w')
	except:
		print 'Output File cannot be found'
		sys.exit()
	for index,line in enumerate(records):
		
		for index,feature in enumerate(line):
			if index = 0:
				fs.write('%s')%feature
			else:
				feature = feature_max[index]-feature_min[index]
		for line in fs.read_lines:
			features = line.split(' ')
			fout.write('')
	for feature in range(1:feature_num):
		fout.write('%s')%label[feature-1]



if __name__=='__main__':
	file_name = sys.argv[1]
	scale(file_name)