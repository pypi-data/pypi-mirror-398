#!/usr/bin/env python

from evHID.hid.kbev import KBEV_Posix as KBEV
from evHID.Types.callback import Callback as Cb
from signal import pause
from time import sleep


## how this shit should work ideallly
# keypress-> triggers event trought device listener
# -> checks for readable on stdin if so the key was meant for us
# -> reads key from the device buffer
# -> uses that to clear number of chars from stdin
# -> key gets added to global buffer
# -> getkey pops last key from buffer
# -> getkeys gets all from buffer and wipes buffer
strings = ['\x1b[2;1Hpress Q to quit.',  # will quit instantly when the program has focus
		   '\x1b[4;{OS}H\x1b[1;34mLOCAL ASYNC DETECT:\x1b[m',
		   '\x1b[5;{OS}H\x1b[1mN   NAME',
		   '\x1b[{C2}GCHAR',
		   '\x1b[{C3}GKEYCODE\x1b[m']

def progress(n):
	print('\x1b[3;1H\x1b[48;2;0;0;0m\x1b[128G\x1b[2K\x1b[3;1H',end='',flush=True)
	# print(''.join(['\x1b[3;{X}H\x1b[48;2;{R};{G};0m  '.format(X=32+(i*2),R=0+(2*i),G=(0+8*j)) for i,j in zip(range(64,32),range(0,64,2))]),end='',flush=True)
	for i in range(256):
		print('\x1b[3;{X}H\x1b[48;2;{R};{G};0m\x1b[1K '.format(X=(i // 2)+1, R=255-i ,G=i), end='',
			  flush=True)
		sleep(0.01)

	for j in range(256):
		i=256-j
		print('\x1b[3;{X}H\x1b[48;2;{R};{G};0m\x1b[1K\x1b[48;2;0;0;0m\x1b[K'.format(X=(i // 2)+1, R=256-i ,
																						G=i),
			  end='',
			  flush=True)
		sleep(0.01)

	print('\x1b[3;32H\x1b[1;48;2;0;0;0;1;38;2;255;255;255m\x1b[5mPRESS HOME KEY TO RESTART\x1b[m',end='',flush=True)



def async_callbackfunction(s,tc=1):
	import sys
	values={'OS':60*tc,'C2':(60*tc)+20,	'C3':(60*tc)+40, }
	for string in strings:
		print(string.format(**values),end='',flush=True)
	row = '\x1b[{1};60H\x1b[K\x1b[3{C}m{N}\x1b[60G{NAME}\x1b[80G{CHR}\x1b[100G0x{V}\x1b[m'
	window=[];n=0
	def kd(key):
		nonlocal window;nonlocal n
		if key == 'q': sys.exit()
		n+=1
		c =(2*int(bin(n)[-1])) +  (5*(not int(bin(n)[-1])))
		window += [row.format(C=c,N=n, NAME=key.name, CHR=key.char, V=key.value)]
		(len(window)>15)*window.pop(0)
		for i, line in enumerate(window):
			print(row.format(i+6,*line))
	return kd



if __name__ == '__main__':
	coll = '\x1b[{};59H\x1b[1K\x1b[G\x1b[1;3{}m{} {}  \x1b[20G{}\x1b[40G0x{}\x1b[m'

	cb = Cb()
	cb.key='end'
	cb.event=[Cb.Event.DOWN,Cb.Event.UP]
	cb.function=async_callbackfunction
	cb.scope+=[Cb.Scope.GLOBAL]



		# **{ 'fn'    :  async_callbackfunction ,
		# 			'event' : 'kd'    ,
		# 			'scope' : 'local',
		# 			'vars'  : {'window': []}})
	tc=0
	Done=False
	with KBEV(cb=cb) as kb:
		print('\x1b[4;{OFFSET}H\x1b[1;32mLOCAL SYNC DETECT::\x1b[m'.format(OFFSET=60*tc))
		print('\x1b[5;{OFFSET}H\x1b[1mN   NAME\x1b[{C2}GCHAR\x1b[{C3}GKEYCODE\x1b[m'.format(OFFSET=60*tc,C2=(60*tc)+20,C3=(60*tc)+40))
		window=[];n=1
		while True:

			if not Done or n%21==0:
				progress(n)
				Done=True

			if kb.event():
				key=kb.key; n+=1
				if key=='home':
					Done=False
					continue
				c=3 if int(bin(n)[-1]) else 4
				window+=[[c,n,key.name,key.char,key.value]]
				if len(window)>5:
					window.pop(0)
				for i,line in enumerate(window):
					print(coll.format(i+6,*line))
			pause()

