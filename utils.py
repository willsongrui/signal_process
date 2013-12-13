import math
import numpy as np

# method 1: absSum
def calVolume(waveData, frameSize, overLap):
    wlen = len(waveData)
    step = frameSize - overLap
    frameNum = int(math.ceil(wlen*1.0/step))
    volume = np.zeros((frameNum,1))
    for i in range(frameNum):
        curFrame = waveData[np.arange(i*step,min(i*step+frameSize,wlen))]
        curFrame = curFrame - np.median(curFrame) # zero-justified
        volume[i] = np.sum(np.abs(curFrame))
    return volume

# method 2: 10 times log10 of square sum
def calVolumeDB(waveData, frameSize, overLap):
    wlen = len(waveData)
    step = frameSize - overLap
    frameNum = int(math.ceil(wlen*1.0/step))
    volume = np.zeros((frameNum,1))
    for i in range(frameNum):
        curFrame = waveData[np.arange(i*step,min(i*step+frameSize,wlen))]
        curFrame = curFrame - np.mean(curFrame) # zero-justified
        volume[i] = 10*np.log10(np.sum(curFrame*curFrame))
    return volume

# Auto-Correlation Function
def ACF(frame):
    flen = len(frame)
    acf = np.zeros(flen)
    for i in range(flen):
    	try:
        	acf[i] = np.dot(frame[i:flen],frame[0:flen-i])
        except:
        	print frame[i:flen]
        	print i,flen
        	raise Exception('Error')

    return acf

# average magnitude difference function
def AMDF(frame):
	flen = len(frame)
	amdf = np.zeros(flen)
	for i in range(flen):
		amdf[i] = np.sum(abs(frame[i:flen]-frame[0:flen-i]))

def isPositive(frame):
    trans = []
    for i in frame:
        if i>=0:
            trans.append(1)
        else:
            trans.append(-1)
    return np.array(trans)