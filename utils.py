import math
import numpy as np
import pylab as pl 
from spectrogram import spectrogram
def plotVolume(m):
    pl.subplot([m.volume,m.absVolume,m.shortTimeEnergy])
def plotPitch(m):
    pitch = []
    pitchValue = []
    end = 0
    for index,r in enumerate(m.speechSegment):
        pitch = pitch + [0]*(r[0]-end) + m.pitch[index]
        pitchValue = pitchValue + [0]*(r[0]-end) + [t[1] for t in m.tmp[index]]
        end = r[1]
    pitch = pitch + [0]*(m.frameNum-m.speechSegment[-1][1])
    pitchValue = pitchValue + [0]*(m.frameNum-m.speechSegment[-1][1])
    pl.subplot(511)
    pl.ylabel('pitch')
    pl.plot(pitch)
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,500],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,500],color='green')
    pl.subplot(512)
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,max(pitchValue)],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,max(pitchValue)],color='green')
    pl.ylabel('value')
    pl.plot(pitchValue)
    pl.subplot(513)
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,max(m.zcr)],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,max(m.zcr)],color='green')
    pl.ylabel('zcr')
    pl.plot(m.zcr)
    pl.subplot(514)
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,1],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,1],color='green')
    pl.ylabel('volume')
    pl.plot(m.absVolume/max(m.absVolume))
    pl.subplot(515)
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,max(m.ezr)],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,max(m.ezr)],color='green')
    pl.ylabel('ezr')
    pl.plot(m.ezr)
    pl.show()

def plot(m):
    pl.plot(m)
    pl.show()
def subplot(m):
    n = len(m)
    n = n*100+10+1
    for k in m:
        pl.subplot(n)
        pl.plot(k)
        n = n+1
    pl.show()
def plotAll(m):
    pitch = []
    end = 0
    for index,r in enumerate(m.speechSegment):
        pitch = pitch + [0]*(r[0]-end) + m.pitch[index]
        end = r[1]
    pitch = pitch + [0]*(m.frameNum-m.speechSegment[-1][1])
    pl.subplot(611)
    pl.plot(m.absVolume)
    #pl.xlabel('Frame Num')
    pl.ylabel('Volume')
    #pl.grid(True)
    for s in m.speechSegment:
        pl.plot([s[0],s[0]],[0,max(m.absVolume)],color='red')
        pl.plot([s[1],s[1]],[0,max(m.absVolume)],color='green')
        
    pl.subplot(612)
    pl.plot(m.zcr)
    pl.ylabel('Zero Cross Rate')
    #pl.xlabel('Frame Num')
    pl.subplot(613)
    pl.plot(pitch)
    #pl.xlabel('Frame Num')
    pl.ylabel('Pitch')
    for index,s in enumerate(m.pitchSeg):
        for p in s:
            pl.plot([p[0]+m.speechSegment[index][0],p[0]+m.speechSegment[index][0]],[0,500],color='red')
            pl.plot([p[1]+m.speechSegment[index][0],p[1]+m.speechSegment[index][0]],[0,500],color='green')
    pl.subplot(614)
    
    
    pl.plot(m.f1)
    pl.ylabel('Formant 1')
    pl.subplot(615)
    spectrogram(m)
    pl.ylabel("spectrogram")
    pl.xlabel('Frame Num')
    pl.subplot(616)
    pl.ylabel("Energy Below 250Hz")
    pl.plot(m.energyBelow250)
    pl.show()

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

def argLocalMax(R):
    result = []
    for r in range(1,len(R)-1):
        if(R[r-1]<R[r] and R[r]>R[r+1]):
            result.append(r)
    return result

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

def zcr(frame,zcrThread):
    n = len(frame)
    cnt = 0
    for i in range(n-1):
        if ((np.sign(frame[i])*np.sign(frame[i+1])<0) and (abs(frame[i]-frame[i+1])>zcrThread)):
            cnt = cnt+1
    return cnt

def advancedACF(frame1,frame2):
    if len(frame1)!=len(frame2):
        return
    frame = frame1+frame2
    flen = len(frame1)
    acf = np.zeros(flen)
    if len(frame1)!=len(frame2):
        return -1
    for k in range(flen/2):
        acf[k] = np.dot(frame[:flen],frame[k:flen+k])
    return acf

# average magnitude difference function
def AMDF(frame):
    flen = len(frame)
    amdf = np.zeros(flen)
    for i in range(flen):
        amdf[i] = np.sum(abs(frame[i:flen]-frame[0:flen-i]))/(flen-i+1)
    return findPitch(amdf)

def findPitch(amdf):
    #print np.argmin(amdf[30:])+30
    return np.argmin(amdf[30:])+30


def complexGreater(a,b):
    return abs(a)**2>abs(b)**2

def isPositive(frame):
    trans = []
    for i in frame:
        if i>=0:
            trans.append(1)
        else:
            trans.append(-1)
    return np.array(trans)