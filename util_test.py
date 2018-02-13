import unittest

import util


class UtilTest(unittest.TestCase):

    def test_RingBuffer_get(self):
        buf = util.RingBuffer(4)
        self.assertEqual([0, 0, 0, 0], buf.get())

    def test_RingBuffer_put_get(self):
        buf = util.RingBuffer(4)
        buf.put(1)
        self.assertEqual([0, 0, 0, 1], buf.get())
        buf.put(2)
        self.assertEqual([0, 0, 1, 2], buf.get())
        buf.put(3)
        self.assertEqual([0, 1, 2, 3], buf.get())
        buf.put(4)
        self.assertEqual([1, 2, 3, 4], buf.get())
        buf.put(5)
        self.assertEqual([2, 3, 4, 5], buf.get())

    def test_to_int16(self):
        self.assertEqual(0x1234, util.to_int16(0x12, 0x34))

        def test_GoogleFormPoster(self):
            poster = util.GoogleFormPoster('https://docs.google.com/forms/d/e/1FAIpQLSePbFzMLyEaQVJ9aW-ZRPYsXO8kfm1ay7khmRADiDz0rondYw/viewform?usp=pp_url&entry.1441205787=1970-01-01&entry.1440681565=00:00&entry.1603777044=0&entry.8655809=1&entry.668218130=2&entry.1797950773=3&entry.1371427267=4&entry.1869212283=5&entry.671273885=6&entry.2022906028=7&entry.18109896=8&entry.1464624802=9&entry.2068592484=10&entry.1601194695=11&entry.1795391290=12')
            self.assertEqual(
                'https://docs.google.com/forms/d/e/1FAIpQLSePbFzMLyEaQVJ9aW-ZRPYsXO8kfm1ay7khmRADiDz0rondYw', poster.prefix)
            self.assertEqual('entry.1464624802', poster.keys[9])
            self.assertEqual('entry.1441205787', poster.keys['date'])

if __name__ == '__main__':
    unittest.main()
