import unittest

from tracker.heartbeat import Heartbeat
from tracker.run import _send_with_heartbeat


class FakeRequest:
    def __init__(self):
        self.values = []
        self.released = False

    def set_value(self, line, value):
        self.values.append((line, value))

    def release(self):
        self.released = True


class TestHeartbeat(unittest.TestCase):
    def test_each_beat_toggles_the_line(self):
        request = FakeRequest()
        heartbeat = Heartbeat(request, 17, "high", "low")

        heartbeat.beat()
        heartbeat.beat()
        heartbeat.beat()

        self.assertEqual(request.values,
                         [(17, "high"), (17, "low"), (17, "high")])

    def test_close_drives_low_before_release(self):
        request = FakeRequest()
        heartbeat = Heartbeat(request, 17, "high", "low")
        heartbeat.beat()

        heartbeat.close()

        self.assertEqual(request.values[-1], (17, "low"))
        self.assertTrue(request.released)

    def test_close_is_safe_to_repeat(self):
        request = FakeRequest()
        heartbeat = Heartbeat(request, 17, "high", "low")

        heartbeat.close()
        heartbeat.close()

        self.assertEqual(request.values, [(17, "low")])

    def test_beat_after_close_is_rejected(self):
        heartbeat = Heartbeat(FakeRequest(), 17, "high", "low")
        heartbeat.close()

        with self.assertRaises(RuntimeError):
            heartbeat.beat()


class FakeHeartbeat:
    def __init__(self):
        self.beats = 0

    def beat(self):
        self.beats += 1


class TestSendGate(unittest.TestCase):
    def test_successful_dmx_send_makes_one_heartbeat(self):
        heartbeat = FakeHeartbeat()

        _send_with_heartbeat(lambda _frame: True, [1, 2, 3], heartbeat)

        self.assertEqual(heartbeat.beats, 1)

    def test_failed_dmx_send_makes_no_heartbeat(self):
        heartbeat = FakeHeartbeat()

        with self.assertRaises(RuntimeError):
            _send_with_heartbeat(lambda _frame: False, [1, 2, 3], heartbeat)

        self.assertEqual(heartbeat.beats, 0)


if __name__ == "__main__":
    unittest.main()
