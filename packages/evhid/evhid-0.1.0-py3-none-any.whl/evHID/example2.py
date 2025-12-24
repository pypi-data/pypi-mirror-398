#!/usr/bin/env python
from evHID.hid.kbev import KBEV_Posix as KBEV
# from evHID.dev.keyboard import KBDev as KBEV
from libTerm import Term
from evHID.Types.callback import  Callback
from signal import pause
import sys
import time
EXIT=0
def cbExit(s):
	def cbexit(key):
		global EXIT
		if key.char == 'q':
			print('q')
			EXIT=1
	return cbexit

cb=Callback(fn=cbExit)
cb.scope+=[Callback.Scope.GLOBAL]
cb.event+=[Callback.Event.DOWN]

term=Term()
print(repr(term.cursor.xy))
with KBEV(term=term,cb=cbExit) as kb:
	i=0
	while not EXIT:
		print(kb.event())
		if kb.event():

			key=kb.key()
			print(kb.key.name)
			if key == 'left':
				print(f'\x1b[10;10H{(i:=i-1)}')
			if key == 'right':
				print(f'\x1b[10;10H{(i:=i+1)}')
		
		pause()