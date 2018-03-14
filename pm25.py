import serial
import time

import util


def parse_pms5003_message(data):
    return [util.to_int16(data[i], data[i + 1]) for i in range(4, 30, 2)]


def is_valid(data):
    return all([len(data) == 32,
                data[0] == 0x42,
                data[1] == 0x4d,
                data[2] == 0x00,
                data[3] == 0x1c,
                sum(data[:-2]) == util.to_int16(*data[-2:]),
                ])


def generate_pms5003_message(max_bytes=1024):
    buf = util.RingBuffer(32)
    bytes_read_since_last_message = 0
    with serial.Serial('/dev/ttyAMA0') as s:
        while True:
            buf.put(ord(s.read()))
            data = buf.get()
            if is_valid(data):
                yield data
                bytes_read_since_last_message = 0
            else:
                bytes_read_since_last_message += 1
                if max_bytes > 0 and bytes_read_since_last_message >= max_bytes:
                    raise RuntimeError(
                        '%d bytes read without seeing a valid PMS5003 message.' % bytes_read_since_last_message)


if __name__ == '__main__':
    throttle = util.Throttle(60)
    poster = util.GoogleFormPoster('https://docs.google.com/forms/d/e/1FAIpQLSePbFzMLyEaQVJ9aW-ZRPYsXO8kfm1ay7khmRADiDz0rondYw/viewform?usp=pp_url&entry.1441205787=1970-01-01&entry.1440681565=00:00&entry.1603777044=0&entry.8655809=1&entry.668218130=2&entry.1797950773=3&entry.1371427267=4&entry.1869212283=5&entry.671273885=6&entry.2022906028=7&entry.18109896=8&entry.1464624802=9&entry.2068592484=10&entry.1601194695=11&entry.1795391290=12')
    status_file = '/tmp/pm25.txt'
    while True:
        try:
            for i in generate_pms5003_message():
                when = time.gmtime()
                ints = parse_pms5003_message(i)
                print(when, ints)
                util.dump(ints[4], status_file)
                print(throttle.maybe_run(lambda: poster.post(when, ints)))
        except Exception as e:
            print(e)
            util.dump('error', status_file)
            time.sleep(1)
