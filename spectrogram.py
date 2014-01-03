"""
Compute and display a spectrogram.
Give WAV file as input
"""
import matplotlib.pyplot as plt
import scipy.io.wavfile
import numpy as np
import sys


def spectrogram(m):
	sr = m.sampleRate
	x = m.rawData
	## Parameters: 10ms step, 30ms window
	#nstep = int(sr * 0.01)
	#nwin  = int(sr * 0.03)
	nstep = m.step
	nwin = m.frameSize
	nfft = nwin
	window = np.hamming(nwin)
	## will take windows x[n1:n2].  generate
	## and loop over n2 such that all frames
	## fit within the waveform
	nn = range(nwin, len(x), nstep)
	X = np.zeros( (len(nn), nfft/2) )
	for i,n in enumerate(nn):
		xseg = x[n-nwin:n]
		z = np.fft.fft(window * xseg, nfft)
		X[i,:] = np.log(np.abs(z[:nfft/2]))

	plt.imshow(X.T, interpolation='nearest',origin='lower',aspect='auto')
