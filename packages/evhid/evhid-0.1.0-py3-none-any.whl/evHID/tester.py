# from hashlib import file_digest
# from operator import truediv
# from os import eventfd
# from select import select
# from evHID.Types.term.posix import Term
# import sys
# from time import sleep
#
# term=Term()
# term.mode('ctl')
# fd=sys.stdin.fileno()
# event=False
# while True:
# 	a,b,c=select([fd], [], [], 0)
# 	if a!=[]:
# 		event=True
# 	if event:
# 		while a!=[]:
# 			a, b, c = select([fd], [], [], 0)
# 			print('\x1b[5;5H\x1b[31mEvent\x1b[m')
# 			cc=sys.stdin.read(1)
# 			print(f'\x1b[6;5H\x1b[31m{cc}\x1b[m')
# 		event=False
#
# 	else:
# 		print('\x1b[5;5H\x1b[32mevent\x1b[m')
# 	sleep(0.05)
#
# import sys
# from select import select
# from time import sleep
# from evHID.Types.term.posix import Term
#
# term = Term()
# term.mode('ctl')
# fd = sys.stdin.fileno()
# buffer=[]
# while True:
# 	event= select([fd], [], [], 0)[0]
#
# 	if event:
# 		print('\x1b[5;5H\x1b[31mEvent\x1b[m')
# 		while event:
# 			buffer+=[c:= sys.stdin.read(1)]
# 			print(f'\x1b[6;5H\x1b[31m{c}\x1b[m')
# 			print(f'\x1b[7;5H\x1b[32m{"".join(buffer)}\x1b[m')
# 			event = select([fd], [], [], 0)[0]
# 	else:
# 		print('\x1b[5;5H\x1b[32mevent\x1b[m')
# 	sleep(0.1)

from __future__ import print_function

import hid
import time

# enumerate USB devices

for d in hid.enumerate():
    keys = list(d.keys())
    keys.sort()
    for key in keys:
        print("%s : %s" % (key, d[key]))
    print()

# try opening a device, then perform write and read
h = hid.device()
try:
    print("Opening the device")
    h.open(6940, 7004)  # TREZOR VendorID/ProductID

    print("Manufacturer: %s" % h.get_manufacturer_string())
    print("Product: %s" % h.get_product_string())
    print("Serial No: %s" % h.get_serial_number_string())
    print("Report descriptor: %s" % h.get_report_descriptor())

    # enable non-blocking mode
    h.set_nonblocking(1)

    # write some data to the device
    print("Write the data")
    h.write([0, 63, 35, 35] + [0] * 61)

    # wait
    time.sleep(0.05)

    # read back the answer
    print("Read the data")
    while True:
        d = h.read(64)
        if d:
            print(d)
        else:
            break

    print("Closing the device")
    h.close()

except IOError as ex:
    print(ex)
    print("hid error:")
    print(h.error())
    print("")
    print("You probably don't have the hard-coded device.")
    print("Update the h.open() line in this script with the one")
    print("from the enumeration list output above and try again.")

print("Done")
