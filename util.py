import calendar
import contextlib
import requests
import time
import urllib

import RPi.GPIO as GPIO  # yaourt -S python-raspberry-gpio


class RingBuffer(object):

    def __init__(self, size):
        self.buf = [0] * size
        self.i = 0

    def put(self, x):
        self.buf[self.i] = x
        self.i = (self.i + 1) % len(self.buf)

    def get(self):
        return self.buf[self.i:] + self.buf[:self.i]


def to_int16(h, l):
    return (h << 8) | l


class GoogleFormPoster(object):

    def __init__(self, url):
        url = urllib.parse.urlparse(url)
        assert url.path.endswith('/viewform')
        self.prefix = url.scheme + '://' + \
            url.netloc + url.path[:-len('/viewform')]
        keys = {}
        for q in url.query.split('&'):
            k, v = q.split('=')
            if k.startswith('entry.'):
                if v == '1970-01-01':
                    keys['date'] = k
                elif v == '00:00':
                    keys['time'] = k
                else:
                    keys[int(v)] = k
        self.keys = keys

    def post(self, when, data):
        params = {}
        for k, v in self.keys.items():
            if k == 'date':
                params[v] = time.strftime('%Y-%m-%d', when)
            elif k == 'time':
                params[v] = time.strftime('%H:%M', when)
            else:
                params[v] = str(data[k])
        post_url = self.prefix + '/formResponse'
        user_agent = {'Referer': self.prefix + '/viewform',
                      'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36"}
        return requests.post(post_url, data=params, headers=user_agent)

class Throttle(object):

    def __init__(self, secs):
        self._secs = secs
        self._last = time.gmtime(0)

    def maybe_run(self, f):
        now = time.gmtime()
        if calendar.timegm(now) - calendar.timegm(self._last) >= self._secs:
            result = f()
            self._last = now
            return result, True
        else:
            return None, False


class InputChannel(object):

    def __init__(self, ch):
        self.ch = ch

    @property
    def get(self):
        return GPIO.input(self.ch)


class OutputChannel(object):

    def __init__(self, ch):
        self.ch = ch

    def put(self, bit):
        GPIO.output(self.ch, bit)


@contextlib.contextmanager
def gpio(inputs=(), outputs=()):
    GPIO.setmode(GPIO.BOARD)
    input_channels = []
    for i in inputs:
        GPIO.setup(i, GPIO.IN)
        input_channels.append(InputChannel(i))
    output_channels = []
    for o in outputs:
        if isinstance(o, tuple):
            o, init = o
        else:
            assert isinstance(o, int)
            o, init = o, 0
        GPIO.setup(o, GPIO.OUT, initial=init)
        output_channels.append(OutputChannel(o))
    yield tuple(input_channels), tuple(output_channels)
    GPIO.cleanup([_.ch for _ in input_channels + output_channels])
