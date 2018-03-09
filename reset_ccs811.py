import smbus2
import sys

import ccs811

address = int(sys.argv[1], 16)
assert address in [0x5a, 0x5b]

with smbus2.SMBusWrapper(1) as bus:
    ccs811.CCS811(bus, address).reset()
