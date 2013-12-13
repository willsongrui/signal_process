import speech_process
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib.pyplot as plt
def usage():
	if len(sys.argv)!=2 and len(sys.argv)!=6:
		print "Usage:\n 	python record_process.py 'record_file' [-cChannelNum] [-rSampleRate] [-wSampleWidth] [-eLittleEndian] [-lLogFile]"
		print "Default Value:\n     -c1 -r8000 -w2 -e1 -llog.txt"
		print "Attention\n       Only PCM records need parameters above"
		


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
record = speech_process.speech_process(sys.argv[1],nchannels=channelNum,sampleRate=sampleRate,sampleWidth=sampleWidth,littleEndian=littleEndian,logFile=logFile)

time  = np.arange(record.frameNum)
plt.subplot(511)
plt.plot(time,record.volume)

plt.subplot(512)
plt.plot(time,record.zcr)
plt.subplot(513)
plt.plot(time,record.shortTimeEnergy)
plt.subplot(514)
plt.specgram(record.rawData,Fs=record.sampleRate,scale_by_freq = True)

time2 = np.arange(len(record.pitch))
plt.subplot(515)
#plt.plot(time2,record.pitch)
plt.show()

	
