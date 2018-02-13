import collections
import smbus2  # pip install smbus2
import time

import util


class Error(collections.namedtuple('Error', ['msg_invalid', 'read_reg_invalid', 'measmode_invalid',
                                             'max_resistance', 'heater_fault', 'heater_supply'])):

    def __new__(cls, byte):
        return super(Error, cls).__new__(cls, msg_invalid=byte & 1,
                                         read_reg_invalid=(byte >> 1) & 1,
                                         measmode_invalid=(byte >> 2) & 1,
                                         max_resistance=(byte >> 3) & 1,
                                         heater_fault=(byte >> 4) & 1,
                                         heater_supply=(byte >> 5) & 1)


class Status(collections.namedtuple('Status',
                                    ['error', 'data_ready', 'app_valid', 'fw_mode'])):

    def __new__(cls, byte):
        return super(Status, cls).__new__(cls, error=byte & 1,
                                          data_ready=(byte >> 3) & 1,
                                          app_valid=(byte >> 4) & 1,
                                          fw_mode=(byte >> 7) & 1)


class Mode(collections.namedtuple('Mode', ['drive_mode', 'interrupt', 'thresh'])):

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and not kwargs:
            byte, = args
            return super(Mode, cls).__new__(cls, drive_mode=(byte >> 4) & 0x7,
                                            interrupt=(byte >> 3) & 1, thresh=(byte >> 2) & 1)
        else:
            return super(Mode, cls).__new__(cls, *args, **kwargs)

    def to_byte(self):
        return ((self.drive_mode & 0x7) << 4 | (self.interrupt & 1) << 3 | (self.thresh & 1) << 2)


class RawData(collections.namedtuple('RawData', ['current', 'voltage'])):

    def __new__(cls, word):
        return super(RawData, cls).__new__(cls, current=word >> 10,
                                           voltage=float(word & 0x20) / 0x20 * 1.65)


class Result(collections.namedtuple('Result', ['e_co2', 'tvoc', 'status', 'error', 'raw'])):

    def __new__(cls, bytes):
        if len(bytes) >= 2:
            e_co2 = util.to_int16(bytes[0], bytes[1])
        else:
            e_co2 = None
        if len(bytes) >= 4:
            tvoc = util.to_int16(bytes[2], bytes[3])
        else:
            tvoc = None
        if len(bytes) >= 5:
            status = Status(bytes[4])
        else:
            status = None
        if len(bytes) >= 6:
            error = Error(bytes[5])
        else:
            error = None
        if len(bytes) == 8:
            raw = RawData(util.to_int16(bytes[6], bytes[7]))
        else:
            raw = None
        return super(Result, cls).__new__(cls, e_co2=e_co2,
                                          tvoc=tvoc, status=status, error=error, raw=raw)


class CCS811(object):

    def __init__(self, bus, addr):
        assert addr in [0x5a, 0x5b]
        self.bus = bus
        self.addr = addr

    def reset(self, wait=0.050):
        self.bus.write_i2c_block_data(
            self.addr, 0xff, [0x11, 0xe5, 0x72, 0x8a])
        time.sleep(wait)

    def is_device(self):
        return self.bus.read_byte_data(self.addr, 0x20) == 0x81

    def status(self):
        return Status(self.bus.read_byte_data(self.addr, 0))

    def error(self):
        return Error(self.bus.read_byte_data(self.addr, 0xe0))

    def start_app(self, wait=0.050):
        self.bus.write_byte(self.addr, 0xf4)
        time.sleep(wait)

    def mode(self):
        return Mode(self.bus.read_byte_data(self.addr, 0x1))

    def _set_mode(self, drive_mode, interrupt=0, thresh=0):
        """Use switch_mode instead"""
        byte = Mode(
            drive_mode=drive_mode, interrupt=interrupt, thresh=thresh).to_byte()
        self.bus.write_byte_data(self.addr, 0x1, byte)

    def switch_mode(self, drive_mode, interrupt=0, thresh=0):
        current_mode = self.mode()
        if (current_mode.drive_mode == drive_mode and current_mode.interrupt == interrupt and current_mode.thresh == thresh):
            return
        # TODO: do we need to wait before switching to mode 4?
        if current_mode.drive_mode and current_mode.drive_mode <= drive_mode:
            print('sleep for 10 minutes before going from mode %d to mode %d' %
                  (current_mode.drive_mode, drive_mode))
            self._set_mode(0)
            time.sleep(10 * 60)
        self._set_mode(drive_mode, interrupt, thresh)

    def result(self):
        return Result(self.bus.read_i2c_block_data(self.addr, 0x2, 8))

    def maybe_start_app(self, max_tries=100):
        num_tries = 0
        while max_tries <= 0 or num_tries < max_tries:
            num_tries += 1
            status = self.status()
            if status.error:
                # This should also clear the error bit
                print(self.error())
            elif not status.app_valid:
                raise RuntimeError('no valid app, reset?')
            elif status.fw_mode:
                # app already running
                return
            else:
                self.start_app()
        raise RuntimeError(
            'failed to start app after %d tries' % num_tries)


def main():
    throttle = util.Throttle(60)
    poster = util.GoogleFormPoster(
        'https://docs.google.com/forms/d/e/1FAIpQLScsxaGES6uXJMzOmJDOpCVJCjaX8EZpAb1HOx6McEIwVqGeFw/viewform?usp=pp_url&entry.806682994=0&entry.1017453344=1&entry.1050656656=2&entry.815754693=3')
    with smbus2.SMBusWrapper(1) as bus:
        dev = CCS811(bus, 0x5a)
        assert dev.is_device()
        dev.maybe_start_app()
        dev.switch_mode(1)
        while True:
            try:
                status = dev.status()
                if status.error:
                    print(dev.error())
                elif status.data_ready:
                    result = dev.result()
                    print(result)
                    print(throttle.maybe_run(lambda: poster.post(
                        None, [result.e_co2, result.tvoc, result.raw.current, result.raw.voltage])))
            except Exception as e:
                print(e)
            time.sleep(1)


if __name__ == '__main__':
    main()
