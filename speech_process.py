from speech import *
frameSize = 256
overLap = 128


def speech_process(source, nchannels=1, sampleRate=8000, sampleWidth=2,littleEndian=1,minLen=3.0,minSilence=1.5,logFile="log.txt"):
	try:
		record = Speech(source,nchannels,sampleRate,sampleWidth,littleEndian)
	except Exception,error:
		print Exception," : ",error
		return

	record.getSpeechSegment(frameSize,overLap,minLen,minSilence)
	record.getFramePitch()
	record.getWordsPerSeg()
	record.getStat()
	record.dump('log.txt')
	
	return record


