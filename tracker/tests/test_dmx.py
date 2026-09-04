"""Tests for the DMX channel arithmetic and frame building.

Nothing here talks to olad. These cover the parts that decide which channel a pump
is on and whether an "off" frame is really off, and both of those want to be right
before any water moves.
"""

import unittest

from tracker import dmx


class TestChannelMap(unittest.TestCase):
    def test_nozzle_one_is_channels_one_to_five(self):
        self.assertEqual(dmx.channel_for(1, "red"), 1)
        self.assertEqual(dmx.channel_for(1, "green"), 2)
        self.assertEqual(dmx.channel_for(1, "blue"), 3)
        self.assertEqual(dmx.channel_for(1, "white"), 4)
        self.assertEqual(dmx.channel_for(1, "height"), 5)

    def test_height_is_always_the_fifth_of_the_group(self):
        for nozzle in range(1, 11):
            self.assertEqual(dmx.channel_for(nozzle, "height"), nozzle * 5)

    def test_second_module_starts_at_fifty_one(self):
        # An HD module is 50 channels, so nozzle 1 of module 2 is channel 51.
        self.assertEqual(dmx.channel_for(1, "red", module=2), 51)
        self.assertEqual(dmx.channel_for(10, "height", module=2), 100)

    def test_role_may_be_an_offset(self):
        self.assertEqual(dmx.channel_for(3, dmx.HEIGHT), 15)

    def test_rejects_nozzle_outside_the_module(self):
        for bad in (0, 11, -1):
            with self.assertRaises(ValueError):
                dmx.channel_for(bad, "height")

    def test_rejects_bad_role_offset(self):
        with self.assertRaises(ValueError):
            dmx.channel_for(1, 5)


class TestFrames(unittest.TestCase):
    def test_blank_frame_is_512_zeros(self):
        frame = dmx.blank_frame()
        self.assertEqual(len(frame), 512)
        self.assertFalse(any(frame))

    def test_frame_with_is_full_length_and_otherwise_zero(self):
        # The point of the whole design: an "off" frame must drive every other
        # slot, not leave it holding whatever it had.
        frame = dmx.frame_with(5, 40)
        self.assertEqual(len(frame), 512)
        self.assertEqual(frame[4], 40)
        self.assertEqual(sum(frame), 40)

    def test_frame_with_clamps(self):
        self.assertEqual(dmx.frame_with(1, 999)[0], 255)
        self.assertEqual(dmx.frame_with(1, -5)[0], 0)

    def test_frame_with_rejects_channel_outside_the_universe(self):
        for bad in (0, 513, -1):
            with self.assertRaises(ValueError):
                dmx.frame_with(bad, 10)


class TestClamp(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(dmx.clamp(-1), 0)
        self.assertEqual(dmx.clamp(256), 255)
        self.assertEqual(dmx.clamp(128), 128)

    def test_ceiling_is_honoured(self):
        # This is what --max does in the jog loop.
        self.assertEqual(dmx.clamp(200, high=40), 40)
        self.assertEqual(dmx.clamp(30, high=40), 30)


class TestSendRefusesShortFrames(unittest.TestCase):
    def test_send_rejects_a_short_buffer_before_touching_ola(self):
        # The check must happen before the ola import, so this passes on the
        # laptop where ola is not installed.
        with self.assertRaises(ValueError):
            dmx.send(bytearray(5))


if __name__ == "__main__":
    unittest.main()
