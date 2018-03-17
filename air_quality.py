#!/usr/bin/env python3

import signal
import threading
import time

import pm25
import ccs811
import ssd1306

stop = threading.Event()

def sigterm_handler(*_):
    print('caught sigterm')
    stop.set()

signal.signal(signal.SIGTERM, sigterm_handler)

threads = [
    threading.Thread(target=ssd1306.display_loop, args=(0x3c, stop)),
    threading.Thread(target=pm25.pm25_loop, args=(stop,)),
    threading.Thread(target=ccs811.ccs811_loop, args=(0x5a, stop)),
    threading.Thread(target=ccs811.ccs811_loop, args=(0x5b, stop))]


for _ in threads:
    _.start()

while not stop.is_set():
    time.sleep(1)

for _ in threads:
    _.join()

print('exit')
