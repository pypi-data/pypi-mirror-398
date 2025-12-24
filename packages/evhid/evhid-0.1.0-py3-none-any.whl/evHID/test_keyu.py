from pynput import keyboard
from signal import pause
from Xlib.XK import _load_keysyms_into_XK
from evHID.Types.kb_key import make_Key
print()
def kd(key):
	# KeyCode.from_char()
	print(key.name,key.value)
	k=make_Key(key)

	print(k.name,k.value,k.char,k.key)


with keyboard.Listener(on_press=kd):
	pause()