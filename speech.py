# -*- coding: utf-8 -*-
import wave
import numpy as np
from math import ceil,log
import utils
import scipy.signal as signal
class Speech:
	def __init__(self,source,nchannels,sampleRate,sampleWidth,littleEndian):
		self.fileName = source
		if source.find('.pcm')!=-1:
			if nchannels==0 or sampleWidth==0 or sampleRate==0 or littleEndian==-1:
				raise Exception('WrongParametersForPCM')
			try:
				fw = open(source,'r')
			except:
				print "File %s  can't be found"%(source)
				raise Exception('FileNotFound')
			self.nchannels = nchannels
			self.sampleRate = sampleRate
			self.sampleWidth = sampleWidth
			rawData = fw.read()
			if sampleWidth==1:
				dtype = np.int8
			elif sampleWidth==2:
				dtype = np.int16
			elif sampleWidth==4:
				dtype = np.int32
			self.rawData = np.fromstring(rawData,dtype=dtype)
			self.nframes = len(self.rawData)
			fw.close()
		elif source.find('.wav')!=-1:
			try:
				fw = wave.open(source,'r')
			except:
				print "File %s  can't be found"%(source)
				raise Exception('FileNotFound')
			params = fw.getparams()
			self.nchannels,self.sampleWidth,self.sampleRate,self.nframes = params[:4]
			rawData = fw.readframes(self.nframes)
			if self.sampleWidth==1:
				dtype = np.int8
			elif self.sampleWidth==2:
				dtype = np.int16
			elif self.sampleWidth==4:
				dtype = np.int32
			self.rawData = np.fromstring(rawData,dtype=dtype)
			fw.close()
		self.rawData = self.rawData*1.0/max(abs(self.rawData))
		self.totalLength = self.nframes*1.0/self.nchannels/self.sampleRate
		self.speechSegment = []
		self.frame = []
		self.zcr = []
		self.shortTimeEnergy = []
		self.volume = []
		self.speed = []

	def __del__(self):
		pass
	
	def getSpeechSegment(self,frameSize,overLap,minLen,minSilence):
		if frameSize<=overLap:
			raise Exception('Wrong getFrames parameters')
		self.frameSize = frameSize
		self.overLap = overLap
		self.step = self.frameSize-self.overLap
		self.frameNum = int(ceil(self.nframes/self.step))
		self.absVolume = []
		for i in range(self.frameNum):
			self.frame.append(self.rawData[i*self.step:min(i*self.step+frameSize,self.nframes)])
			#get zeroCrossingRate and energy
			#self.zcr.append(sum(self.frame[i][0:-1]*self.frame[i][1:]<=0))
			zeroFrame = utils.isPositive(self.frame[i])
			self.zcr.append(0.5*sum(abs(zeroFrame[0:-1]-zeroFrame[1:])))
			self.shortTimeEnergy.append(sum([k**2 for k in self.frame[i]]))
			cal = sum(self.frame[i]*self.frame[i])
			if cal==0:
				cal = 0.001
			self.volume.append(10*np.log(cal))
			self.absVolume.append(sum(abs(self.frame[i])))
		# Two threadholds for shortTimeEnergy 
		tHoldLow = min(max(self.shortTimeEnergy)/8,2)
		tHoldHigh = min(max(self.shortTimeEnergy)/4,10)
		self.tHoldHigh = tHoldHigh
		self.tHoldLow = tHoldLow
		self.segmentTime = []
		# status is used to show the status of the endPointDetection machine
		# 0=>silence		1=>mayBegin		2=>speechSegment 	3=>end 
		status = 0
		count = 0
		segmentBeg = 0  
		silence = 0		#Used to indicate the length of silence frames 
		minSilence = int(minSilence*self.sampleRate/self.frameSize)  #If we meet minSilence consecutive silence than the speech is probably end
		minLen = int(minLen*self.sampleRate/self.frameSize) 	#A speech should at least longer than minLen frames
		segmentEnd = 0
		#print  "minSilence",minSilence,"minLen",minLen
		for i in range(self.frameNum):
			if (status == 0) or (status == 1):
				if self.shortTimeEnergy[i]>tHoldHigh:
					segmentBeg = i-count
					status = 2
					silence = 0
					count = count + 1
					#print "beg"
				elif self.shortTimeEnergy[i]>tHoldLow:
					status = 1
					count = count + 1
				else:
					status = 0
					count = 0
			elif status == 2:
				if self.shortTimeEnergy[i] > tHoldLow:
					count = count + 1
					silence = 0
				else:
					silence = silence + 1
					if silence < minSilence:	#silence is not long enough to end the speech
						count = count + 1
					elif count < minLen:		#speech is so short that it should be  noise
						status = 0
						silence = 0
						count = 0
						#print "endOfNoise"
					else:
						status = 0
						segmentEnd = i - minSilence
						self.speechSegment.append((segmentBeg,segmentEnd))
						self.segmentTime.append((segmentBeg*self.totalLength/self.frameNum,segmentEnd*self.totalLength/self.frameNum))
						#print "beg speech %d %f"%(segmentBeg,segmentBeg*self.totalLength/self.frameNum)
						#print "end speech %d %f"%(segmentEnd,segmentEnd*self.totalLength/self.frameNum)
						status = 0
						count = 0
						silence = 0
		if status == 2:
			self.speechSegment.append((segmentBeg,self.frameNum))
			self.segmentTime.append((segmentBeg*1.0/self.sampleRate,self.frameNum*1.0/self.sampleRate))
			#self.segmentTime.append((self.frameNum-segmentBeg)*1.0/self.sampleRate)	
		self.speechTime = sum([v[1]-v[0] for v in self.segmentTime])
		self.totalSeg = len(self.speechSegment)
	def getFramePitch(self):
		pitchLow = self.sampleRate/800
		self.pitch = []
		for segTime in self.speechSegment:
			pitchSum = 0
			beg = segTime[0]
			end = segTime[1]
			curFramePitch = []
			for frame in self.frame[beg:end]:
				pitch = utils.ACF(frame)
				pitch[:pitchLow] = -pitch[0]
				pitchMax = np.argmax(pitch)
				curFramePitch.append(self.sampleRate/pitchMax)
			self.pitch.append(curFramePitch)

	def freqAnalyze(self):
		self.fftFrame = []
		h1,f1 = signal.freqz([1,-0.98],[1])
		for frame in self.frame[:-1]:
			#窗函数
			f = frame*signal.hamming(self.frameSize,sym=0)
			fftFrame = np.fft.rfft(f)/self.frameSize
			#预加重
			fftFrame = f1[:len(fftFrame)]*fftFrame
			self.fftFrame.append(fftFrame)
	
	def getWordsPerSeg(self,minLen=3,minSilence=2,preLen=2):
		status = 0 
		self.segWord = []
		for seg in self.speechSegment:
			segBeg = seg[0]
			segEnd = seg[1]
			volumeHigh = max(self.volume)/4
			volumeLow = max(self.volume)/8
			zcrHigh = max(self.zcr)/4
			zcrLow = max(self.zcr)/8
			#print volumeHigh,volumeLow
			word = 0
			segWord = []
			count = 0
			precount = 0
			crest = 0
			wordBeg = 0
			for frame in range(segBeg,segEnd):
				if status==0 or status==1:
					crest = max(crest,self.volume[frame])
					if self.volume[frame] >= volumeHigh:
						status = 2
						count = precount + 1
						wordBeg = frame-count
						#print "begin",frame
					elif self.volume[frame] >= volumeLow:
						status = 1
						precount = precount + 1
						if precount >= preLen:
							status = 2
							#print "begin",frame
							wordBeg = frame-precount
							count = precount
							precount = 0
					else:
						precount = 0
						status = 0
				elif status == 2:
					crest = max(crest,self.volume[frame])
					#print "crest",crest
					if self.volume[frame] >= volumeLow and self.volume[frame]>= crest/2:
						count = count + 1
						silence = 0
					else:
						silence = silence + 1
						if silence > minSilence:
							status = 0
							crest = 0
							if frame-wordBeg+1 > minLen:
								word = word + 1
								segWord.append((wordBeg,frame))
								#print "end success",frame
							else:
								pass
								#print "end of too short",frame
							precount = 0
							count = 0
			if status == 2:
				segWord.append((wordBeg,segEnd))
			self.segWord.append(segWord)
			#print segWord
			self.speed.append(len(segWord)*1.0/((segEnd-segBeg)*1.0*(self.frameSize-self.overLap)/self.sampleRate))

	def getStat(self):
		self.totalWord = 0
		self.stat = []
		#otalVolume = int(sum(self.volume)/self.frameNum)
		#self.totalPitch = int(sum(self.pitch)/self.frameNum)
		self.averagePitch = 0
		self.averageVolume = 0
		speechFrameNum = 0
		
		for i in range(len(self.speechSegment)):
			self.totalWord = self.totalWord + len(self.segWord[i])
			self.averagePitch = sum(self.pitch[i]) + self.averagePitch
			segBeg = self.speechSegment[i][0]
			segEnd = self.speechSegment[i][1]
			self.averageVolume = self.averageVolume + sum(self.absVolume[segBeg:segEnd])
			speechFrameNum = speechFrameNum + segEnd - segBeg
			shortTimeEnergy = int(sum(self.shortTimeEnergy[segBeg:segEnd])/(segEnd-segBeg))
			volume = float(sum(self.absVolume[segBeg:segEnd])/(segEnd-segBeg))
			pitch = float(sum(self.pitch[i])/(segEnd-segBeg))
			speed = float(self.speed[i])
			item = {"volume":volume,"pitch":pitch,"speed":speed,"shortTimeEnergy":shortTimeEnergy,"time":self.segmentTime[i][1]-self.segmentTime[i][0],"words":len(self.segWord[i])}
			self.stat.append(item)
		self.speechFrameNum = speechFrameNum
		self.averagePitch = self.averagePitch/self.speechFrameNum
		self.averageVolume = self.averageVolume/self.speechFrameNum
		self.averageSpeed = self.totalWord*1.0/self.speechTime
		self.volumeVariance = sum([(v['volume']-self.averageVolume)*(v['volume']-self.averageVolume) for v in self.stat])/len(self.speechSegment)
		self.pitchVariance = sum([(v['pitch']-self.averagePitch)*(v['pitch']-self.averagePitch) for v in self.stat])/len(self.speechSegment)
		self.speedVariance = sum([(v['speed']-self.averageSpeed)*(v['speed']-self.averageSpeed) for v in self.stat])/len(self.speechSegment)
		self.segNum = len(self.speechSegment)
		self.timeLen = self.nframes/self.sampleRate/self.nchannels
	def dump(self,log_file):
		fs = open(log_file,'aw')
		fileName = self.fileName.split('/')[-1]
		fs.write('%-20s%-15d%-15.2f%-15.2f%-15.2f%-15d%-15f\n'%(fileName,self.segNum,self.averageSpeed,self.averagePitch,self.averageVolume,self.totalWord,self.speechTime))
		#totalStat = ""
		#totalStat = str(self.fileName)+"  "+str(self.totalWord)+"  "+str(self.averageVolume)+"  "+str(self.averagePitch)+"\n"
		#fs.write(totalStat)
		
		segNum = 0
		for stat in self.stat:
			segNum = segNum + 1
			fs.write('%-20s%-15d%-15.2f%-15.2f%-15.2f%-15d%-15.2f\n'%("",segNum,stat['speed'],stat['pitch'],stat['volume'],stat['words'],stat['time']))
			
		fs.write('%-20s%-15s%-15.2f%-15.2f%-15.2f\n'%("","Variance",self.speedVariance,self.pitchVariance,self.volumeVariance))
		fs.close()

	def pre_getWordsPerSeg(self, a=2, T=3):
		self.transitionTag = []
		for seg in self.speechSegment:
			segBeg = seg[0]
			segEnd = seg[1]
			TshortTimeEnergyBefore = sum(self.speechSegment[segBeg:segBeg+3])
			TshortTimeEnergyAfter = sum(self.speechSegment[segBeg+2:segBeg+5])
			for k in xrange(segBeg+2,segEnd-4):
				curShortEnergy = self.shortTimeEnergy[k]
				curZcr = self.zcr[k]
				flag = False
				if curShortEnergy>a*self.shortTimeEnergy[k+1] or curShortEnergy*a<self.shortTimeEnergy[k+1]:
					flag = True
				elif curZcr>a*self.zcr[k+1] or curZcr*a<self.zcr[k+1]:
					flag = True
				elif TshortTimeEnergyBefore*a < TshortTimeEnergyAfter or TshortTimeEnergyAfter*a < TshortTimeEnergyBefore:
					flag = True
				if flag == True:
					self.transitionTag.append(k)
				TshortTimeEnergyBefore = TshortTimeEnergyBefore - self.shortTimeEnergy[k-2] + self.shortTimeEnergy[k+1]
				TshortTimeEnergyAfter = TshortTimeEnergyAfter - self.shortTimeEnergy[k] + self.shortTimeEnergy[k+3]



