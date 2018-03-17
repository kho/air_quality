import re
import smbus2
import subprocess
import time

import font5x8
import util

class SSD1306Device(object):

    def __init__(self, bus, addr):
        self.bus = bus
        self.addr = addr

    def command(self, *bs):
        # print('command', ' '.join(map(hex, bs)))
        self.bus.write_i2c_block_data(self.addr, 0, bs)

    def data(self, *bs):
        for i in range(0, len(bs), 32):
            self.bus.write_i2c_block_data(self.addr, 0x40, bs[i:i+32])

    # 4. Hardware configuration

    def set_display_line_start(self, start=0):
        assert start >= 0 and start < 64
        self.command((1 << 6) | start)

    def set_segment_remap(self, addr_127=False):
        self.command(0xa0 + addr_127)

    def set_mux_ratio(self, ratio_minus_1=0x3f):
        assert ratio_minus_1 >= 0xf and ratio_minus_1 <= 0x3f
        self.command(0xa8, ratio_minus_1)

    def set_com_output_scan_direction(self, high_to_low=False):
        self.command(0xc0 | (high_to_low << 3))

    def set_display_offset(self, offset=0):
        assert offset >= 0 and offset < 64
        self.command(0xd3, offset)

    def set_com_pins(self, sequential=False, left_right_remap=False):
        self.command(0xda, (left_right_remap<<5) | (sequential<<4) | 0x2)

    # 5. Timing & driving scheme setting

    def set_osc_freq(self, freq=0x8, divide_ratio=0):
        assert freq >= 0 and freq <= 0xf
        assert divide_ratio >= 0 and divide_ratio <= 0xf
        self.command(0xd5, (freq<<4) | divide_ratio)

    def set_pre_charge_period(self, phase1=2, phase2=2):
        assert phase1 >= 0 and phase1 <= 0xf
        assert phase2 >= 0 and phase2 <= 0xf
        self.command(0xd9, (phase2<<4) | phase1)

    def set_v_comh_deselect_level(self, level=0x20):
        assert level in (0, 0x20, 0x30)
        self.command(0xdb, level)

    # Charge pump

    def set_charge_pump(self, on=False):
        self.command(0x8d, 0x10 | (on << 2))

    def off(self):
        self.command(0xae)
        time.sleep(0.1)

    def on(self):
        self.command(0xaf)
        time.sleep(0.1)

    def set_contrast(self, contrast=0x7f):
        assert contrast >= 0 and contrast <= 0x7f
        self.command(0x81, contrast)

    def set_all_on(self, all_on=True):
        self.command(0xa4 + all_on)

    def set_invert(self, invert=True):
        self.command(0xa6 + invert)

    def set_addressing_mode(self, mode=0):
        '''
        mode: 0 horizontal 1 vertical 2 page
        '''
        assert mode in (0, 1, 2)
        self.command(0x20, mode)

    def set_column_address(self, low=0, high=0x7f):
        assert 0 <= low and low <= high and high <= 0x7f
        self.command(0x21, low, high)

    def set_page_address(self, low=0, high=7):
        assert 0 <= low and low <= high and high <= 7
        self.command(0x22, low, high)

    def set_all(self, b=0):
        self.set_addressing_mode()
        self.set_column_address()
        self.set_page_address()
        self.data(*([b] * 128 * 8))

    def initialize(self):
        self.off()
        self.set_mux_ratio()
        self.set_display_offset()
        self.set_display_line_start()
        # Flip display
        self.set_segment_remap(True)
        self.set_com_output_scan_direction(True)
        self.set_com_pins(sequential=False)
        self.set_contrast()
        self.set_all_on(False)
        self.set_invert(False)
        self.set_osc_freq()
        self.set_charge_pump(True)
        self.on()
        self.set_all(0)
        time.sleep(0.5)
        self.set_all(0xff)
        time.sleep(0.5)
        self.set_all(0)


    def draw1(self, col_start=0x10, col_end=0x1f, page_start=2, page_end=5):
        self.set_column_address(col_start, col_end)
        self.set_page_address(page_start, page_end)
        num_cols = col_end - col_start + 1
        num_pages = page_end - page_start + 1
        while True:
            for i in [0xff, 0xf, 0]:
                repeat = 2
                for _ in range(num_cols * num_pages // repeat):
                    self.data(*([i]*repeat))
                    time.sleep(0.1)

    def draw2(self):
        self.puts('This is a very long string with lots of letters. ~~~>_<~~~ @_@')
        n = 0
        while True:
            self.puts(hex(n), row=1, col=2, wrap=True)
            n += 1

    def puts(self, s, row=0, col=0, clear=True, wrap=False):
        font = font5x8.Font5x8
        height = font.rows
        width = font.cols
        assert height == 8
        padding = 1
        while 128 % (width + padding) != 0:
            padding += 1
        padded_width = width + padding
        bs = []
        for i in s:
            offset = ord(i) * width
            bs.extend(font.bytes[offset:offset + width])
            bs.extend([0] * padding)
        if clear:
            bs.extend([0] * (128 - (col + len(s)) * padded_width))
        col_start = col * padded_width
        if not wrap:
            bs = bs[:128 - col_start]
        for r in [row, row + 4]:
            self.set_page_address(r)
            self.set_column_address(col_start)
            self.data(*bs)

class Display(object):

    UNK = '???'

    def __init__(self, dev):
        self._dev = dev

    def get_ip(self):
        try:
            stdout = str(subprocess.check_output(['ip', 'addr', 'show', 'dev', 'eth0']))
        except:
            return self.UNK
        ip = re.search('inet ([0-9.]*)/', stdout)
        if ip:
            return ip.group(1)
        else:
            return self.UNK

    def read_file(self, path):
        try:
            with open(path) as f:
                return f.read().strip()
        except:
            return self.UNK

    def run(self, stop=None):
        while stop is None or not stop.is_set():
            try:
                self._dev.puts('IP:' + self.get_ip(), row=0)
                self._dev.puts('PM25:' + self.read_file('/tmp/pm25.txt'), row=1)
                self._dev.puts('TVOC(a):' + self.read_file('/tmp/tvoc.0x5a.txt'), row=2)
                self._dev.puts('TVOC(b):' + self.read_file('/tmp/tvoc.0x5b.txt'), row=3)
            except Exception as e:
                print(e)
            time.sleep(1)
        print('exit ssd1306')

def display_loop(addr, stop=None):
    with util.flock('/tmp/ssd1306.{}.lock'.format(hex(addr))):
        with smbus2.SMBusWrapper(1) as bus:
            dev = SSD1306Device(bus, addr)
            dev.initialize()
            print('init done')
            try:
                Display(dev).run(stop)
            finally:
                dev.off()

if __name__ == '__main__':
    display_loop(0x3c)
