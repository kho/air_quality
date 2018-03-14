#!/usr/bin/env python3

import threading

import pm25
import ccs811
import ssd1306

threads = [
    threading.Thread(target=pm25.pm25_loop),
    threading.Thread(target=ccs811.ccs811_loop, args=(0x5a,)),
    threading.Thread(target=ccs811.ccs811_loop, args=(0x5b,)),
    threading.Thread(target=ssd1306.display_loop, args=(0x3c,))]

for _ in threads:
    _.start()

for _ in threads:
    _.join()

