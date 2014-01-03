from speech import *
frameSize = 256
overLap = 128


def speech_process(source, nchannels=1, sampleRate=8000, sampleWidth=2,littleEndian=1,minLen=0.2,minSilence=0.3,logFile="log.txt",dataFile="/home/will/Documents/data.txt",label='0'):
	try:
		record = Speech(source,nchannels,sampleRate,sampleWidth,littleEndian)
	except Exception,error:
		print Exception," : ",error
		return

	record.getSpeechSegmentByAbsVolume(frameSize,overLap,minLen,minSilence)
	record.energyZeroCount()
	record.getFramePitch()
	record.getWordsPerSeg()
	record.freqAnalyze()
	record.LPC()
	record.getEnergyBelow250()
	
	record.getStat()
	record.dataProcess()
	record.dump('log.txt')
	record.writeToFile(dataFile,label)
	
	return record


