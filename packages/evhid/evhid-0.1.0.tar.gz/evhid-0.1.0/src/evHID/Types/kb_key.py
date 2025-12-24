from dataclasses import dataclass,field
from pynput import keyboard
from enum import Enum
class KbEvent(Enum):
	INIT = 'init'
	DOWN = 'down'
	UP = 'up'

@dataclass(frozen=True)
class Key():
	__qualname__ = keyboard.Key.__name__
	key: keyboard.Key
	name: str
	char: str
	value: int
	event: KbEvent = field(default=KbEvent.INIT)
	def __missing__(__s,missing):
		return getattr(__s.key,missing,None)
	def __str__(__s):
		return str(__s.key).strip("'")

	def __repr__(__s):
		return f'key({__s.name},{__s.value},\'{__s.char}\')'

	def __int__(__s):
		return __s.value

	def __eq__(__s, other):
		matcha= [__s,__s.key, __s.name, __s.char, __s.value ]
		matcha+=[str(i) for i in matcha]
		matcha+=[repr(i) for i in matcha]
		return other in matcha

def make_Key(key):
	return FKey(key).makeKey()


@dataclass()
class FKey() :
	_key: keyboard.Key
	_name: str = field(default='')
	_char: str = field(default='')
	_value: int = field(default=0)
	_down: bool = field(default=False)
	_up: bool = field(default=True)

	# _term:int=field(default=0)
	def __post_init__(__s):
		tmp={}
		for attr in ["char", "value", "name"]:
			 tmp[attr]=getattr(__s._key, attr, None)
		missing = [name for name in ("char", "value", "name") if getattr(__s, f'_{name}', None) is None]
		if "char" in missing:
			__s.char = getattr(__s._key, "name", str(__s._key))
		if 'value' in missing:
			value = ord(getattr(__s._key, "char"))
			if value is None:
				value=str(__s.key)
			__s.value=value
		if 'name' in missing:
			__s.name = __s.char
		if __s.name == 'space':
			__s.char=' '
			__s.value= 0x20
	def makeKey(s):
		return Key(s.key, s.name, s.char, s.value)
	@property
	def key(__s):
		return __s._key

	@key.setter
	def key(__s, key):
		__s._key = key

	@property
	def value(__s):
		return __s._value

	@value.setter
	def value(__s, value):
		__s._value = int(str(value).strip('<').strip('>'))
		print(__s._value)

	@property
	def char(__s):
		return __s._char

	@char.setter
	def char(__s, char):
		__s._char = char

	@property
	def name(__s):
		return __s._name

	@name.setter
	def name(__s, name):
		__s._name = name


