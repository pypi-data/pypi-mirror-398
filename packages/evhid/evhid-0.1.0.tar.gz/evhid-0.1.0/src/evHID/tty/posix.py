#!/usr/bin/env python
import sys
from select import select
from signal import SIGUSR1
import os


class KBTty():
	def __init__(__s,parent=None,term=None):
		# super().__init__()
		__s.parent=parent
		__s.term=parent.term if parent else term
		__s._buffer=[]
		__s._event=True
		__s._count=0

	@property
	def event(s):
		s._event=select([s.term.fd], [], [], 0)[0]!=[]
		return s._event
		# print(__s._count)
		# print(('====='*int(__s._event))+('+++++'*(not __s._event)))

		# if event:
		# 	while event:
		# 		__s._buffer += [sys.stdin.read(1)]
		# 		event = select([__s.term.fd], [], [], 0)[0]

	
	def read(__s):
		ret=None
		if __s.event:
			while __s.event:
				__s._buffer += [sys.stdin.read(1)]
			ret=''.join( __s._buffer)
			__s._buffer=[]
			__s._count+=1
		return ret
	def counted(s):
		return '\x1b[2;1H\x1b[3{}m{}\x1b[m'.format(int(bin(s._count)[-1])+1,s._count)
	def getch(__s):
		if len(__s.buffer)!=0:
			c=__s.buffer[-1]
			__s.flush()
	def flush(__s):
		__s.buffer=[]
		sys.stdin.flush()





