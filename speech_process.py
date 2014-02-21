from speech import *
frameSize = 256
overLap = 128


def speech_process(source, nchannels=1, sampleRate=8000, sampleWidth=2,littleEndian=1,minLen=0.2,minSilence=0.3,feature_file="/home/will/Documents/data.txt",label='0'):
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
	#record.LPC()
	record.getEnergyBelow250()
	record.getSpeechPercentage()
	record.dataProcess()
	record.writeToFile(feature_file,label)
	
	return record



def predict(record,scale_model='scale_model',model_file='train_model',label_file='records_information'):
	record.predict(scale_model,model_file,label_file)


