from pynput import keyboard
from time import sleep
def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False



listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()
while True:
    sleep(0.001)