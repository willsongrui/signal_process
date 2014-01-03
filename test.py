import speech_process
import pylab as pl 
m=speech_process.speech_process('50/angry-2/201.wav')
pl.subplot(211)
pl.plot(m.absVolume)
pl.subplot(212)
pl.plot(m.zcr)
pl.show()