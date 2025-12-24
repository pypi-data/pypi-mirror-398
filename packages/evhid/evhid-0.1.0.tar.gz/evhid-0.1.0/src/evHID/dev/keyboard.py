#!/usr/bin/env python
import os
from signal import SIGUSR1
from pynput import keyboard
from evHID.Types.kb_key import make_Key,KbEvent
from evHID.Types.kb_key import KbEvent as Event

class KBDev():
	def __init__(s,**k):
		s.sig=SIGUSR1
		s.listen=keyboard.Listener
		s.parent=k.pop('parent',None)
		s.__kwargs__(**k)
		s._key=None
		s._keys_down=set()
		s._keys_hist=[None,]
		s.__create__()

	def __kwargs__(s,**k):
		s._callbacks=k.get('cb')

	def __keydown__(s):
		def kdn(key):
			fkey=make_Key(key)
			print(fkey)
			return fkey
		return kdn
		# s.parent.setkey(fkey)
		# s.signal__()


	def __keyup__(s):
		def kup(key):
			fkey=make_Key(key)
			print(fkey)
			return fkey
		return kup



	def __create__(s):

		cb={'on_press':s.__keydown__(),
			'on_release':s.__keyup__()
			}
		s.listener = s.listen(**cb)
		s.start=s.listener.start
		s.join=s.listener.join
		s.stop=s.listener.stop
		return s

	def __enter__(s):
		s.__create__()
		s.start()
		return s


	def __exit__(s,*a,**k):
		s.stop()

	def __buildin_kd__(s):
		key=s._key
		s._keys_down=set([*s._keys_down,key])
		s._keys_hist+=[key]

	def __buildin_ku__(s,key):
		if isinstance(key,EventKey):
			key=key.key

		s._keys_down-=set([key,])


	def signal__(s):
		os.kill(s.term.pid, s.sig)

	def addcallback(s,cb):
		if cb.event == 'kd':
			s.cb['kd']+=[cb]
		if cb.event == 'ku':
			s.cb['ku']+=[cb]
	@property
	def key(s):
		key=s._key
		s._key=None
		return key

	@key.setter
	def key(s,key):
		s._key=key

