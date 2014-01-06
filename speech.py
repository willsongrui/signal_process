# -*- coding: utf-8 -*-
import os
import math
import wave
import numpy as np
from math import ceil,log
import utils
import scipy.signal as signal
from scipy.signal import argrelmax
import scipy

from audiolazy import *
import pylab as pl
from scikits.talkbox import lpc as talkboxLpc
from mood_svm import classify
class Speech:
	def __init__(self,source,nchannels,sampleRate,sampleWidth,littleEndian):
		self.error = []
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
		maxData = max(abs(self.rawData))
		print maxData
		if maxData<2000:
			self.isBlank = True
		else:
			self.isBlank = False
		self.maxData = maxData
		#self.rawData = self.rawData*1.0/maxData
		self.rawData = self.rawData*1.0
		self.totalLength = self.nframes*1.0/self.nchannels/self.sampleRate
		self.speechSegment = []
		self.frame = []
		self.zcr = []
		self.shortTimeEnergy = []
		self.volume = []
		self.speed = []

	def __del__(self):
		pass
	
	def getSingleWords(self):
		pass
	def getEnergyBelow250(self):
		self.energyBelow250 = []
		loc = int(250.0/4000*self.frameSize)
		for fftFrame in self.fftFrameAbs:
			totalEnergy = np.sum(fftFrame)
			below250 = np.sum(fftFrame[:loc])
			self.energyBelow250.append(below250/totalEnergy)

	# get speechSegment,volume,volumeAbs,and shortTimeEnergy 
	def getSpeechPercentage(self):
		self.speechPercentage = 0
		speechFrame = 0
		for i in self.speechSegment:
			speechFrame = speechFrame + i[1] - i[0]
		self.speechPercentage = speechFrame*1.0/self.frameNum 
		self.speechLength = self.speechPercentage*self.totalLength
	def getSpeechSegment(self,frameSize,overLap,minLen,minSilence):
		print "getSpeechSegment"
		zcrThread = 0
		if self.isBlank == True:
			return
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
			#zeroFrame = utils.isPositive(self.frame[i])
			#zcrThread = max(self.frame[i])/2
			zcrThread = 1000000
			zcr = utils.zcr(self.frame[i],zcrThread)
			self.zcr.append(zcr)
			#self.zcr.append(0.5*sum(abs(zeroFrame[0:-1]-zeroFrame[1:])))
			self.shortTimeEnergy.append(sum([k**2 for k in self.frame[i]]))
			cal = sum(self.frame[i]*self.frame[i]*1.0/self.maxData/self.maxData)
			if cal==0:
				cal = 0.001
			self.volume.append(10*np.log(cal))
			self.absVolume.append(sum(abs(self.frame[i])))
		# Two threadholds for shortTimeEnergy 
		tHoldLow = min(max(self.shortTimeEnergy)/8,1)
		tHoldHigh = min(max(self.shortTimeEnergy)/4,4)
		print '*****'
		print tHoldLow
		print tHoldHigh
		self.tHoldHigh = tHoldHigh
		self.tHoldLow = tHoldLow
		print self.tHoldHigh
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
		print  "minSilence",minSilence,"minLen",minLen
		for i in range(self.frameNum):
			if (status == 0) or (status == 1):
				if self.shortTimeEnergy[i]>tHoldHigh:
					segmentBeg = i-count
					status = 2
					silence = 0
					count = count + 1
					print "beg"
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
						print "endOfNoise"
					else:
						status = 0
						segmentEnd = i - minSilence
						self.speechSegment.append((segmentBeg,segmentEnd))
						self.segmentTime.append((segmentBeg*self.totalLength/self.frameNum,segmentEnd*self.totalLength/self.frameNum))
						print "end success"
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
	
	def energyZeroCount(self):
		self.ezr = []
		self.ezm = []
		for i in range(len(self.shortTimeEnergy)):
			if self.zcr[i]!=0:
				ezr = self.shortTimeEnergy[i]/self.zcr[i]/10000000
			else:
				ezr = self.shortTimeEnergy[i]/10000000
			ezm = self.shortTimeEnergy[i]*self.zcr[i]/10000000
			self.ezr.append(ezr)
			self.ezm.append(ezm)

	def getSpeechSegmentByAbsVolume(self,frameSize,overLap,minLen,minSilence):
		print "getSpeechSegment"
		zcrThread = 0
		if self.isBlank == True:
			return
		if frameSize<=overLap:
			raise Exception('Wrong getFrames parameters')
		self.frameSize = frameSize
		self.overLap = overLap
		self.step = self.frameSize-self.overLap
		self.frameNum = int(ceil(self.nframes/self.step))
		self.absVolume = []
		for i in range(self.frameNum):
			self.frame.append(self.rawData[i*self.step:min(i*self.step+frameSize,self.nframes)])
			zcrThread = max(self.frame[i])/8
			#get zeroCrossingRate and energy
			#self.zcr.append(sum(self.frame[i][0:-1]*self.frame[i][1:]<=0))
			#zeroFrame = utils.isPositive(self.frame[i])
			zcr = utils.zcr(self.frame[i],zcrThread)
			self.zcr.append(zcr)
			self.shortTimeEnergy.append(sum([k**2 for k in self.frame[i]]))
			cal = np.sum(self.frame[i]*self.frame[i]*1.0/self.maxData/self.maxData)
			if cal==0:
				cal = 0.001
			self.volume.append(10*np.log(cal))
			self.absVolume.append(np.sum(np.abs(self.frame[i])))
		# Two threadholds for shortTimeEnergy 
		tHoldLow = min(max(self.absVolume)/10,3*self.maxData)
		tHoldHigh = min(max(self.absVolume)/6,6*self.maxData)
		self.tHoldHigh = tHoldHigh
		self.tHoldLow = tHoldLow
		#print self.tHoldHigh
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
				if self.absVolume[i]>tHoldHigh:
					segmentBeg = i-count
					status = 2
					silence = 0
					count = count + 1
					#print "beg"
				elif self.absVolume[i]>tHoldLow:
					status = 1
					count = count + 1
				else:
					status = 0
					count = 0
			elif status == 2:
				if self.absVolume[i] > tHoldLow:
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
						#print "end success"
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

	#50Hz ~ 450Hz
	#为了消除共振峰的影响，使用带通滤波器(60~900)或中心削波
	def getFramePitch(self):
		#放浊音基音的开始和结尾
		#pitchSeg is used to store the "ZHUOYIN" pitch seg of Each speechSeg,its length is the same as self.speechSeg
		#For example, self.pitchSeg[m][n] is the (n+1)th "ZHUOYIN" pitch seg in m+1 speechSeg 
		self.pitchSeg = []
		#self.tmp = []
		minLen = 5 # 最小浊音长度
		minSilence = 5 #浊音之间最小间隔
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		
		pitchThread = int(self.sampleRate/450)
		self.pitch = []
		self.tmp=[]
		for segTime in self.speechSegment:
			tmp = []
			pitchSum = 0
			beg = segTime[0]
			end = segTime[1]
			curFramePitch = []
			for frame in self.frame[beg:end]:
				pitch = utils.ACF(frame)
				#pl.plot(pitch)
				#pl.show()
				pitch[:pitchThread] = -abs(pitch[0])
				
				pitchMax = np.argmax(pitch)
				if pitchMax==0:
					self.error.append(('pitch error',pitch,utils.ACF(frame)))
				tmp.append((self.sampleRate/pitchMax,pitch[pitchMax]/1000000))
				curFramePitch.append(self.sampleRate/pitchMax)
			self.tmp.append(tmp)	
			pitchHigh = np.max(tmp,0)[1]/12.0
			pitchLow = np.max(tmp,0)[1]/24.0
			#pitchHigh = 0
			#pitchLow = 0
			ezrLevel = max(self.ezr[beg:end])*0.2
			volumeHigh = np.max(self.absVolume[beg:end])/4
			volumeLow = volumeHigh/2
			
			#zcrHigh = np.max(self.zcr[beg:end])/2
			#zcrLow = zcrHigh/1
			zcrHigh = 1000
			zcrLow = 1000
			#0 => 清音 1=>可能是浊音 2=>浊音 3=>浊音结束
			status = 0
			trange = []
			count = 0
			silence = 0
			self.pitch.append(curFramePitch)
			print 'ezrLevel',ezrLevel,'volumeHigh',volumeHigh,'pitchHigh',pitchHigh,'minSilence',minSilence,'minLen',minLen
			for t in range(len(tmp)):
				if tmp[t][1]>pitchHigh and self.ezr[t+beg]>ezrLevel:
					print 'beg ',t,'status',status
					if status == 0:
						start = t 
						duration = 0
						status = 1
					duration = duration+1
				else:
					if status == 1:
						trange.append((start,t))
						status = 0
						duration = 0
			if status == 1:
				trange.append((start,len(tmp)))
			self.pitchSeg.append(trange)
			self.tmp.append(tmp)




			'''
			status = 0
			for t in range(len(tmp)):
				if status==0 or status==1:
					if tmp[t][1]>pitchHigh and self.ezr[t+beg]>ezrLevel and self.absVolume[t+beg]>volumeHigh and self.zcr[t+beg]<zcrLow:
						pitchBeg = t-count 
						status = 2
						count = count+1
						print 'beg',t-count
					elif tmp[t][1]>pitchLow and self.ezr[t+beg]>ezrLevel and self.absVolume[t+beg]>volumeLow and self.zcr[t+beg]<zcrHigh:
						status = 1
						count = count+1
					else:
						status = 0
						count = 0
				elif status == 2:
					if tmp[t][1]>pitchLow and self.ezr[t+beg]>ezrLevel and self.absVolume[t+beg]>volumeLow and self.zcr[t+beg]<zcrHigh:
						count = count+1
						silence = 0
					else:
						silence = silence+1
						if silence<minSilence:
							count = count+1
						elif count < minLen:
							status = 0
							silence = 0
							count = 0
							print 'too short',pitchBeg,t			
						else:
							status = 0
							pitchEnd = t - minSilence
							trange.append((pitchBeg,pitchEnd))
							status = 0
							count = 0
							silence = 0
			if status == 2:
				if len(tmp)-pitchBeg > minLen:
					trange.append((pitchBeg,len(tmp)-1))

			self.pitchSeg.append(trange)

			#pitchSeg = []
			#for t in trange:
			#	pitchSeg.append(tmp[t[0]:t[1]])
			#self.pitchSeg.append(pitchSeg)
			
			
			#self.tmp.append(tmp)
			'''
	
	def getFramePitchAdvanced(self):
		pitchLow = 10
		self.pitchAdvanced = []
		for segTime in self.speechSegment:
			pitchAdvanced = []
			beg = segTime[0]
			end = segTime[1]
			for i in range(beg,end):
				pitch = utils.advancedACF(self.frame[i],self.frame[i+1])
				pitch[:pitchLow] = -pitch[0]
				pitchMax = np.argmax(pitch)
				pitchAdvanced.append(self.sampleRate/pitchMax)
		self.pitchAdvanced.append(pitchAdvanced)

	def LPC(self):
		print "LPC"
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		self.ar = []
		self.fmt = []
		self.bw = []
		self.frqs = []
		for frame in self.frame:
			#[ar, var, reflec] = yulewalker.aryule(frame, 8)
			[ar,var,reflec] = talkboxLpc(frame,8)
			self.ar.append(ar)
			rts = np.roots(ar)
			rts = [r for r in rts if np.imag(r)>=0]
			#angz = np.atan2(np.imag(rts),np.real(rts))
			angz = np.asarray([math.atan2(np.imag(r),np.real(r)) for r in rts])
			angz = angz*self.sampleRate/(np.pi*2)
			#print angz
			#[frqs,indices] = sort(angz)
			frqs = [(angz[i],i) for i in range(len(angz))]
			frqs.sort()
			self.frqs.append(frqs)
			fmt = []
			bandwidth = []
			for kk in range(len(frqs)):
				bw = -1.0/2*(self.sampleRate/(2*np.pi))*np.log(np.abs(rts[frqs[kk][1]]))
				#print frqs[kk][0],bw
				if ((frqs[kk][0]>90) and (bw<400) ):
					fmt.append(frqs[kk][0])
					#print frqs[kk][0]
					bandwidth.append(bw)

			fmt.sort()
			fmt = fmt[:3]
			self.fmt.append(fmt)
			self.bw.append(bandwidth)
		self.f1 = []
		for f in self.fmt:
			if len(f)==0:
				self.f1.append(0)
			else:
				self.f1.append(f[0])

	def freqAnalyze(self):
		print "freqAnalyze"
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		self.shortTimeLinjieVector = []
		self.formant = []
		self.fftFrameAbs = []
		#短时谱的临界带特征矢量
		F = [0]
		fs = self.sampleRate/self.frameSize
		for i in range(1,19):
			m = int((i+0.53)*1960/(26.81-0.53-i))
			n = m/fs
			F.append(n)
		
		
		self.formantValue = []
		self.frameSize/2+1
		self.fftFrame = []
		#h1,f1 = signal.freqz([1,-0.98],[1])
		#cc = 0
		for frame in self.frame[:-1]:
			#窗函数
			#cc = cc+1
			f = frame*signal.hamming(self.frameSize,sym=0)
			#预加重
			#f = scipy.signal.lfilter([1,-0.97],1,f)
			fftFrame = np.fft.rfft(f)/(self.frameSize/2)
			self.fftFrame.append(fftFrame)
			fftFrameAbs = [abs(fft) for fft in fftFrame]
			self.fftFrameAbs.append(fftFrameAbs)
			#短时谱临界带特征矢量
			g = np.zeros(17)
			beg = 1
		
			for i in range(1,17):
				for k in range(beg,min(len(fftFrame),F[i]+1)):
					g[i] = g[i] + abs(fftFrame[k])**2
				beg = F[i]+1
			self.shortTimeLinjieVector.append(g)
			#共振峰
			g0 = utils.argLocalMax(fftFrameAbs)
			points = [(fftFrameAbs[g],g) for g in g0]
			points.sort()
			#print g0[0]
			m = min(3,len(g0))
			formant = []
			for i in range(m):
				formant.append(points[-i-1][1]*fs)

			self.formantValue.append(points[-1][0])
			formant.sort() 
			self.formant.append(formant)
	#3,2
	def getWordsPerSeg(self,minLen=10,minSilence=5,preLen=2):
		print "getWordsPerSeg"
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		status = 0 
		self.segWord = []
		for seg in self.speechSegment:
			status = 0
			silence = 0
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
	

	def dataProcess(self):
		#self.maxData = 1
		#语速 基音频率 基音范围 最大基频 最小基频 基频一阶差分绝对值平均值 振幅 振幅标准差 振幅最大值 在250Hz能量以下所占百分比 第一共振峰 第一共振峰范围
		#self.speed self.pitchAverage self.pitchRange, self.volumeAverage self.volumeStd self.fmtAverage  self.fmtRange
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		self.num = len(self.speechSegment)
		
		#for i in range(self.num):
		#	pitchAverage = np.average(self.pitchSeg)
		print "We have %d speech segments in all"%self.num
		self.pitchAverage = 0
		self.pitchAveragePerSeg = []
		self.pitchRange = []
		self.volumeAverage = []
		self.volumeStd = []
		self.fmtAverage = []
		self.pitchMax = []
		self.pitchMin = []
		self.pitchStd = []
		self.volumeMax = []
		self.volumeMin = []
		self.volumeDiff = []
		self.pitchDiff = []
		self.below250 = []
		self.pitchNum = 0
		#self.fmtRange = []
		for i in range(self.num):
			pitchSum = 0
			pitchNum = 0
			pitchMax = 0
			pitchMin = 1000
			pitchDiff = 0
			for k in range(len(self.pitchSeg[i])):
				#print k
				#pitchSeg 是记录在pitch中满足50～450之间的pitch的起始点的 可以用来计算pitch的变化规律
				pitchSum = pitchSum + sum(self.pitch[i][self.pitchSeg[i][k][0]:self.pitchSeg[i][k][1]])
				pitchNum = pitchNum + self.pitchSeg[i][k][1] - self.pitchSeg[i][k][0]
				  
				if self.pitchSeg[i][k][0]==self.pitchSeg[i][k][1]:
					print self.fileName
				pitchMax = max(max(self.pitch[i][self.pitchSeg[i][k][0]:self.pitchSeg[i][k][1]]),pitchMax)
				pitchMin = min(min(self.pitch[i][self.pitchSeg[i][k][0]:self.pitchSeg[i][k][1]]),pitchMin)
				if k!=len(self.pitchSeg[i])-1:
					pitchDiff = pitchDiff + abs(self.pitch[i][k+1]-self.pitch[i][k])
				
					
				#print pitchSum
				#print pitchNum
			if pitchNum==0:
				self.pitchAveragePerSeg.append(0)
				self.pitchRange.append(0)
				self.pitchMax.append(0)
				self.pitchMin.append(0)
				self.pitchDiff.append(0)
				continue
			self.pitchAverage = self.pitchAverage + pitchSum
			self.pitchNum = self.pitchNum + pitchNum
			self.pitchAveragePerSeg.append(pitchSum*1.0/pitchNum)
			pitchDiff = pitchDiff*1.0/pitchNum
			self.pitchDiff.append(pitchDiff)
			self.pitchRange.append((pitchMax-pitchMin))
			self.pitchMax.append(pitchMax)
			self.pitchMin.append(pitchMin)

		if self.pitchNum!=0:
			self.pitchAverage = self.pitchAverage/self.pitchNum
		for i in range(self.num):
			beg = self.speechSegment[i][0]
			end = self.speechSegment[i][1]
			below250 = np.average(self.energyBelow250[beg:end])
			self.below250.append(below250)
			volume = np.average(self.absVolume[beg:end])
			volumeStd = np.std(self.absVolume[beg:end])
			fmtAverage = np.average(self.f1[beg:end])
			self.volumeAverage.append(volume)
			self.volumeStd.append(volumeStd)
			self.volumeMax.append(np.max(self.absVolume[beg:end]))
			self.volumeMin.append(np.min(self.absVolume[beg:end]))
			self.fmtAverage.append(fmtAverage)
			volumeDiff = 0
			for k in range(beg,end-1):
				volumeDiff = volumeDiff + abs(self.absVolume[k+1]-self.absVolume[k])
			self.volumeDiff.append(volumeDiff*1.0/(end-beg))
		self.features = []
		for i in range(self.num):
			features = [self.pitchMax[i],self.pitchAveragePerSeg[i],self.pitchRange[i],self.pitchMin[i],self.pitchDiff[i],self.volumeAverage[i],self.volumeStd[i],self.volumeMax[i],self.volumeDiff[i],self.below250[i]]
			self.features.append(features)
		
	
	def predict(self,scale_model,model_file,label_file):
		self.gender = 'Unknown'
		self.category = -1
		predict_data = 'predict_data'
		#全静音 单交互正常挂机 单交互异常挂机 多交互正常挂机 多交互异常挂机
		if self.isBlank==True:
			self.category = '全静音'
		else:
			if self.pitchAverage in range(100,200):
				self.gender = '男'
			elif self.pitchAverage > 200:
				self.gender = '女'
			self.writeToFile(predict_data,'0')
			self.labels = classify(scale_model,model_file,predict_data)
			cmd = 'rm %s'%predict_data
			os.system(cmd)
		fs = open(label_file,'aw')
		if len(self.labels)==1:
			if self.labels[0]==-1:
				self.category = '单交互正常挂机'
			else:
				self.category = '单交互异常挂机'
		else:
			for label in self.labels:
				if label == 1:
					self.category = '多交互异常挂机'
					break
			if self.category == -1:
				self.category = '多交互异常挂机'
		self.label = np.average(self.labels)
		
		fs.write('File:		%s\nCategory:		%s\nLabel:		%s\n'%(self.fileName,self.category,self.labels))
		#fs.write('%-20s%-20s%-20s%-20s%-20s%-20s\n'%('总时长','通话时长','通话段数','通话人音量','通话人性别','通话人语调'))
		fs.write('总时长        通话时长        通话段数        通话人音量        通话人性别        通话人语调\n')
		fs.write('%-15.2f%-15.2f%-15f%-18.2f%-16s%-20.2f\n'%(self.totalLength,self.speechLength,self.num,np.average(self.volumeAverage),self.gender,self.pitchAverage))
		fs.close()


				
				



	
	
	#用于机器学习
	def writeToFile(self,dataFile,label='0'):
	#基音频率 基音范围 振幅 振幅标准差 第一共振峰 第一共振峰范围
	#pitchAverage pitchRange pitchMax pitchMin pitchDiff volumeMax volumeAverage volumeStd volumeDiff below250 
		fs = open(dataFile,'aw')
		cnt = 1
		#fs.write(self.fileName+'\n')
		if self.isBlank==True:
			fs.write('%s %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f\n'%('0',1,0,2,0,3,0,4,0,5,0,6,0,7,0,8,0,9,0,10,0))
		else:
			for i in range(self.num):
				#fs.write('Wav File Name:%s\n'%(self.fileName))
		#		fs.write('Segment Num %d:\n'%(cnt))
				cnt = cnt + 1
				fs.write('%s %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f %d:%f\n'%(label,1,self.pitchMax[i],2,self.pitchAveragePerSeg[i],3,self.pitchRange[i],4,self.pitchMin[i],5,self.pitchDiff[i],6,self.volumeAverage[i],7,self.volumeStd[i],8,self.volumeMax[i],9,self.volumeDiff[i],10,self.below250[i]))
		
		fs.close()
'''			
	def lpc(self):
		print "lpc"
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		self.numerator = []
		for frame in self.frame:
			acdata = acorr(frame)
			filt = levinson_durbin(acdata,8)
			self.numerator.append(filt.numerator)


'''
'''
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

	def dump(self,log_file):
		fs = open(log_file,'aw')
		fileName = self.fileName.split('/')[-1]
		if len(self.speechSegment)==0 or self.isBlank==True:
			fs.write('%-20s%-15s\n'%(fileName,'全静音'))
			fs.close()
			return
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

	def getStat(self):
		print "getStat"
		if len(self.speechSegment)==0 or self.isBlank==True:
			return
		print len(self.speechSegment)
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
		self.averagePitch = self.averagePitch/(self.speechFrameNum+0.01)
		self.averageVolume = self.averageVolume/(self.speechFrameNum+0.01)
		self.averageSpeed = self.totalWord*1.0/(self.speechTime+0.01)
		self.volumeVariance = sum([(v['volume']-self.averageVolume)*(v['volume']-self.averageVolume) for v in self.stat])/len(self.speechSegment)
		self.pitchVariance = sum([(v['pitch']-self.averagePitch)*(v['pitch']-self.averagePitch) for v in self.stat])/len(self.speechSegment)
		self.speedVariance = sum([(v['speed']-self.averageSpeed)*(v['speed']-self.averageSpeed) for v in self.stat])/len(self.speechSegment)
		self.segNum = len(self.speechSegment)
		self.timeLen = self.nframes/self.sampleRate/self.nchannels
		print "total words:",self.totalWord

'''