import speech_process
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def usage():
	if len(sys.argv)!=2 and len(sys.argv)!=6:
		print "Usage:\n 	python record_process.py 'record_file' [-cChannelNum] [-rSampleRate] [-wSampleWidth] [-eLittleEndian] [-lLogFile]"
		print "Default Value:\n     -c1 -r8000 -w2 -e1 -llog.txt"
		print "Attention\n       Only PCM records need parameters above"
		
def record_process(recordFile,logFile,channelNum,sampleRate,sampleWidth,littleEndian):
	speech_process.speech_process(recordFile,nchannels=channelNum,sampleRate=sampleRate,sampleWidth=sampleWidth,littleEndian=littleEndian,logFile=logFile)

if __name__ == '__main__':
	if len(sys.argv)<2:
		usage()
		sys.exit()
	recordFile = sys.argv[1]

	logFile = 'log.txt'
	channelNum = 1
	sampleRate = 8000
	sampleWidth = 2
	littleEndian = 1
	for arg in sys.argv[2:]:
		if arg.startswith('-c'):
			channelNum = int(arg[2:])
		elif arg.startswith('-r'):
			sampleRate = int(arg[2:])
		elif arg.startswith('-w'):
			sampleWidth = int(arg[2:])
		elif arg.startswith('-e'):
			littleEndian = int(arg[2:])
		elif arg.startswith('-l'):
			logFile = str(arg[2:])
		else:
			print "Unrecgonize parameter :%s"%arg
			usage()
			sys.exit()
	record_process(recordFile,logFile,channelNum,sampleRate,sampleWidth,littleEndian)
		
