import numpy as np
from numpy.random import rand as rand
from matplotlib import pyplot as plt
#from gist import peakdetect
#import lpc_signal
from scipy.io import wavfile
from scipy import signal

def lpc(frame, p):
   x = frame
   R = lambda k: auto_corr(x, k)
   a = np.zeros((p+1, p+1))
   k = np.zeros(p+1)

   E = np.concatenate(([R(0)], np.empty(p)))
   for i in xrange(1, p + 1):
      c = 0
      for j in xrange(1, i):
         c += a[j, i-1] * R(i-j)
      k[i] = (R(i) - c) / E[i-1]

      a[i][i] = k[i]

      for j in xrange(1, i):
         a[j][i] = a[j][i-1] - k[i] * a[i-j][i-1]

      E[i] = (1 - k[i]**2) * E[i-1]

   fa = np.empty(p+1)
   fa[0] = 1
   for j in xrange(1, p+1):
      fa[j] = -a[j][p]
   return fa, E[p]