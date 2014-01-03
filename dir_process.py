import os
import sys
import speech_process
def usage():
	print "Used to process wav in a labeled directory "
	print "python dir_process.py directory label"
if len(sys.argv)<4 :
	usage()
	sys.exit()
if os.path.isdir(sys.argv[1])==False:
	print "%s is not a directory"&sys.arg[1]
	sys.exit()
out = sys.argv[3]
path = sys.argv[1]
files = os.listdir(path)
label = sys.argv[2]
print label
if path.endswith('/')==False:
	path = path + '/'

for f in files:
	print f
	f = path + f
	speech_process.speech_process(f,label=label,dataFile=out)