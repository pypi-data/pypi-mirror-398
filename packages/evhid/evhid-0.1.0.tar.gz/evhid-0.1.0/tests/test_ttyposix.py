# /usr/bin/env pyhthon
from evHID.tty import KBTty



with KBTty() as kb:
	while True:
		if kb.event:
			key=kb.getch()
			print(key)
			if key=='q':
				break
