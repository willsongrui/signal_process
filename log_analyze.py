#coding=utf-8
import os
import sys
def evaluate(a,b,c):
	return (a+b+c)/3

def usage():
	pass

def log_analyze(log_input,log_output,sortStrategy,sortNum):
	try:
		fs = open(log_input,'r')
	except:
		print "File not Found"
		sys.exit()
	flag = False
	variance = []
	recordNum = 0
	for line in fs.readlines():
		if flag==True:
			count = count + 1
			if count==speechNum+1:
				p = line.split()
				item = [record,float(p[1]),float(p[2]),float(p[3])]
				variance.append(item)
				recordNum = recordNum + 1
				flag = False
				continue
		words = line.split()
		if len(words)<=0:
			continue
		if words[0].endswith('pcm') or words[0].endswith('wav'):
			#print words
			flag = True
			record = words[0]
			speechNum = int(words[1])
			count = 0
	if sortStrategy!=4:
		variance=sorted(variance,key=lambda v:v[sortStrategy],reverse=True)
	else:
		speedMax = max([v[1] for v in variance])
		pitchMax = max([v[2] for v in variance])
		volumeMax = max([v[3] for v in variance])
		for v in variance:
			a = v[1]/speedMax
			b = v[2]/pitchMax
			c = v[3]/volumeMax
			rank = evaluate(a,b,c)
			v.append(rank)
		variance = sorted(variance,key=lambda v:v[4],reverse=True)

	if sortNum=='INF':
		sortNum = recordNum

	variance = variance[:sortNum]

	fs = open(log_output,'w')
	if sortStrategy==1:
		strategy = '最大语速方差'
	elif sortStrategy==2:
		strategy='最大语调方差'
	elif sortStrategy==3:
		strategy='最大音量方差'
	else:
		strategy='综合'
	info = '				根据%s策略得到%d条记录\n'%(strategy,recordNum)
	fs.write(info)
	info ='%-21s%-18s%-18s%-15s\n'%('文件名','语速','语调','音量')
	fs.write(info)
	for v in variance:
		info = '%-17s%-15.2f%-15.2f%-15.2f\n'%(v[0],v[1],v[2],v[3])
		fs.write(info)
	fs.close()

if __name__=='__main__':
	if len(sys.argv)<2:
		usage()
		sys.exit()
	sortStrategy = 4
	sortNum = 'INF'
	log_input = 'NULL'
	log_output = 'NULL'

	for arg in sys.argv[1:]:
		if arg.startswith('-n'):
			sortNum = int(arg[2:])
		elif arg.startswith('-s'):
			sortStrategy = 1
		elif arg.startswith('-p'):
			sortStrategy = 2
		elif arg.startswith('-v'):
			sortStrategy = 3
		elif arg.startswith('-i'):
			log_input = arg[2:]
		elif arg.startswith('-o'):
			log_output = arg[2:]
		else:
			usage()
			sys.exit()
	if sortNum != 'INF' and sortNum < 1:
		print '排序记录数指定错误'
		usage()
		sys.exit()
	if log_input=='NULL' or log_output=='NULL':
		print '没有指定输入和输出文件'
		usage()
		sys.exit()
	#print log_input,log_output,sortStrategy,sortNum
	log_analyze(log_input,log_output,sortStrategy,sortNum)

