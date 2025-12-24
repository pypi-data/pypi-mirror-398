#/usr/bin/env pyhthon
from enum import Enum
from typing import Literal

from pynput import keyboard

from enum import Enum
from typing import Literal

from pynput import keyboard


# class Callback():
# 	class Scope(Enum):
# 		GLOBAL = "global"
# 		APPLICATION = "application"
# 		LOCAL = "local"
#
# 	class Event(Enum):
# 		INIT = 'init'
# 		DOWN = 'down'
# 		UP = 'up'
# 	locked:bool
# 	scope: Literal["global", "application", "local"]  #
# 	event: Literal['down', 'up']
# 	match: keyboard.Key
# 	results: list
# 	_uservars: dict
# 	_userfn: callable
# 	_callfn: callable
#
# 	def __init__(s, *a, **k):
# 		s.locked=False
# 		s.scope: list[Callback.Scope] = [Callback.Scope.LOCAL, ]
# 		s.event: list[Callback.Event] = [Callback.Event.DOWN, ]
# 		s.match: keyboard.key = k.get('key')
# 		s.results = []
# 		s._uservars = dict = k.get('vars', k.get('uservars', {}))
# 		s._userfn = callable = k.get('function', k.get('fn'))
# 		s.armed = callable = None
# 		if len(s._uservars) > 0:
# 			s.uservars(s._uservars)
#
#
# 	@property
# 	def function(__s):
# 		return __s._userfn
#
# 	@function.setter
# 	def function(__s, function):
# 		__s._userfn = function
# 		__s.__arm__()
#
# 	def __call__(s, *a, **k):
#
# 		if s.locked:
# 			s.results += [s.armed(*a, **k)]
# 		else:
# 			s.__arm__(*a,**k)
# 		return s.results
# 	def __arm__(s,*a,**k):
# 		s.caller=k.get('caller')
# 		s.armed = s._userfn(s)
# 		s.locked=True
#
# 	def uservars(s, **vars):
# 		for var in vars:
# 			setattr(s, var, vars.get(var))
# 		s.__arm__()
# 		return s._uservars
# #
#
class Callback():
	class Scope(Enum):
		GLOBAL = "global"
		APPLICATION = "application"
		LOCAL = "local"
	class Event(Enum):
		INIT = 'init'
		DOWN = 'down'
		UP   = 'up'

	scope: Literal["global", "application", "local"]  #
	event: Literal['down','up']
	match: keyboard.Key
	results:list
	_uservars: dict
	_userfn: callable
	_callfn: callable
	def __init__(s,*a,**k):
		s.scope : list[Callback.Scope]= [Callback.Scope.LOCAL,]
		s.event : list[Callback.Event] = [Callback.Event.DOWN,]
		s.match : keyboard.key = k.get('key')
		s.results=[]
		s._uservars=k.get('vars',k.get('uservars',{}))
		s._userfn = k.get('function',k.get('fn',lambda e:...))
		s.armed:callable =  None
		if len(s._uservars) > 0:
			s.uservars(s._uservars)
		s.__arm__()


	@property
	def function(__s):
		return __s._userfn
	@function.setter
	def function(__s,function):
		__s._userfn = function
		__s.__arm__()

	def __call__(s, *a,**k):
		s.results+=[s.armed(*a,**k)]

	def __arm__(s):
		s.armed=s._userfn(s)

	def uservars(s,**vars):
		for var in vars:
			setattr(s, var, vars.get(var))
		s.__arm__()
		return s._uservars
