import random
import unittest

import ccs811


def random8():
    return random.randrange(0, 1 << 8)


def random16():
    return random.randrange(0, 1 << 16)


class StatusTest(unittest.TestCase):

    def test_status_error(self):
        for i in range(1000):
            byte = 1 | random8()
            status = ccs811.Status(byte)
            self.assertTrue(status.error, msg='byte=' + hex(byte))
            byte = ~1 & random8()
            status = ccs811.Status(byte)
            self.assertFalse(status.error, msg='byte=' + hex(byte))

    def test_status_data_ready(self):
        for i in range(1000):
            byte = 0x8 | random8()
            status = ccs811.Status(byte)
            self.assertTrue(status.data_ready, msg='byte=' + hex(byte))
            byte = ~0x8 & random8()
            status = ccs811.Status(byte)
            self.assertFalse(status.data_ready, msg='byte=' + hex(byte))

    def test_status_app_valid(self):
        for i in range(1000):
            byte = 0x10 | random8()
            status = ccs811.Status(byte)
            self.assertTrue(status.app_valid, msg='byte=' + hex(byte))
            byte = ~0x10 & random8()
            status = ccs811.Status(byte)
            self.assertFalse(status.app_valid, msg='byte=' + hex(byte))

    def test_status_fw_mode(self):
        for i in range(1000):
            byte = 0x80 | random8()
            status = ccs811.Status(byte)
            self.assertTrue(status.fw_mode, msg='byte=' + hex(byte))
            byte = ~0x80 & random8()
            status = ccs811.Status(byte)
            self.assertFalse(status.fw_mode, msg='byte=' + hex(byte))


class RawDataTest(unittest.TestCase):

    def test_raw_data(self):
        raw = ccs811.RawData(0b1010101010101010)
        self.assertEqual(0b101010, raw.current)
        self.assertEqual(0b1010101010, raw.voltage)


if __name__ == '__main__':
    unittest.main()
