#!/usr/bin/env python
from signal import signal, SIGUSR1
from evHID.Types.callback import Callback
from libTerm import Term
from evHID.tty.posix import KBTty
from evHID.dev.keyboard import KBDev


def Prt(s):
	def prt(key):
		nonlocal s
		k = s.key
		print('key=', key)
		print('k=', k)
	return prt
loccb = Callback(fn=Prt)
class KBEV_Posix():
	def __init__(__s,*a,**k):
		super().__init__()
		__s.term = 	k.get('term',Term())
		__s.calllist= []
		__s.call= []
		__s.mode=__s.__mode__
		__s._dev = KBDev
		__s._tty = KBTty
		__s._key=None
		__s._event=False
		__s._focus=True
		__s.noevkeys=['shift', 'alt', 'ctrl', 'caps_lock', 'cmd', 'num_lock', 'shift_r', 'ctrl_r', 'alt_r','cmd_r']
		__s.dev=__s._dev(parent=__s)
		__s.tty=__s._tty(__s)
		__s.handlers=__s.__sigrecv__()
		__s.__callbacks__()

	def __callbacks__(s):
		for cb in s.calllist:
			s.call+=[cb(s)]

	def __sigrecv__(__s):
		def receive_dev(signum, stack):
			print(signum,stack)
			key=__s.dev.key
			focusev=__s.tty.event
			if not focusev:
				__s._focus= __s._focus if (key.name  in __s.noevkeys) else False
			else :
				__s._focus=True
			if __s._focus:
				__s._chars=__s.tty.read()
				for cb in __s.call:
					cb(key)
				__s._event=True

		__s.s1=signal(SIGUSR1, receive_dev)

	def __create__(__s):
		__s.mode(1)
		__s.dev=__s._dev(parent=__s)
		__s.start=__s.dev.start
		__s.join=__s.dev.join
		__s.stop=__s.dev.stop
	
	def __enter__(__s):
		__s.__create__()
		__s.dev.__enter__()
		return __s
		
	def __exit__(__s,*a,**k):
		__s.dev.__exit__()

	def __mode__(__s,n):
		print('setting terminal to ctl')
		__s.term.mode('ctl')

	@property
	def key(s):
		print(s.dev.key)
		print(s._key)
		return s._key

	def setkey(__s,key):
		__s._key=key
		return key

	def keys(__s):
		key=__s._key
		__s._key=None
		return key
	# if key == K.space:
	def event(__s):
		ev=__s._event
		__s._event=False
		return ev

	# def __update_callbacks__(s):
	# 	for cb in s._callbacks:
	# 		for scope in  cb.scope:
	# 			for surface
	# 			for event in cb.scope:
	# 	if 'global' in cb.scope:
	# 		if 'kd' in cb.event:
	# 			s.cb['glob']['kd']+=[cb]
	# 		if 'ku' in cb.event:
	# 			s.cb['glob']['ku']+=[cb]
	#
	# 	if 'local' in cb.scope:
	# 		if 'kd' in cb.event:
	# 			s.cb['locl']['kd']+=[cb]
	# 		if 'ku' in cb.event:
	# 			s.cb['locl']['ku']+=[cb]

	# @propety
	# def callbacks(s):
	# 	return s._callbacks
	# @callbacks.setter
	# def callbacks(s,cb):
	# 	s._callbacks+=[cb]
	# 	s.__update_callbacks__()
	# @property
	# def callback(s):
	# 	return s._callbacks
	# @callback.setter
	# def callback(s,cb):
	# 	s._callbacks+=[cb]
	# 	s.__update_callbacks__()

