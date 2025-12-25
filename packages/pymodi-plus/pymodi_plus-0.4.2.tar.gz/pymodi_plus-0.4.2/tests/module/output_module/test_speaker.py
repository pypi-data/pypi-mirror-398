import unittest

from modi_plus.module.output_module.speaker import Speaker
from modi_plus.util.message_util import parse_set_property_message, parse_get_property_message
from modi_plus.util.unittest_util import MockConnection, MockSpeaker


class TestSpeaker(unittest.TestCase):
    """Tests for 'Speaker' class."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.connection = MockConnection()
        self.mock_kwargs = [-1, -1, self.connection]
        self.speaker = MockSpeaker(*self.mock_kwargs)

    def tearDown(self):
        """Tear down test fixtures, if any."""

        del self.speaker

    def test_set_tune(self):
        """Test set_tune method."""

        mock_frequency, mock_volume = 500, 30
        self.speaker.tune = mock_frequency, mock_volume
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_SET_TUNE,
            (("u16", mock_frequency), ("u16", mock_volume), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_set_tune_str(self):
        """Test set_tune method."""

        mock_note = Speaker.preset_notes()[0]
        mock_frequency, mock_volume = Speaker.SCALE_TABLE[mock_note], 30
        self.speaker.tune = mock_note, mock_volume
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_SET_TUNE,
            (("u16", mock_frequency), ("u16", mock_volume), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_get_tune(self):
        """Test get_tune method."""

        _ = self.speaker.tune
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Speaker.PROPERTY_SPEAKER_STATE, self.speaker.prop_samp_freq)
        )
        self.assertEqual(_, (0, 0))

    def test_set_frequency(self):
        """Test set_frequency method."""

        mock_frequency = 500
        self.speaker.frequency = mock_frequency
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_SET_TUNE,
            (("u16", mock_frequency), ("u16", 0), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_get_frequency(self):
        """Test get_frequency method with none input."""

        _ = self.speaker.frequency
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Speaker.PROPERTY_SPEAKER_STATE, self.speaker.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_set_volume(self):
        """Test set_volume method."""

        mock_volume = 30
        self.speaker.volume = 30
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_SET_TUNE,
            (("u16", 0), ("u16", mock_volume), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_get_volume(self):
        """Test get_volume method with none input."""

        _ = self.speaker.volume
        self.assertEqual(
            self.connection.send_list[0],
            parse_get_property_message(-1, Speaker.PROPERTY_SPEAKER_STATE, self.speaker.prop_samp_freq)
        )
        self.assertEqual(_, 0)

    def test_play_music(self):
        """Test play_music method."""

        mock_music = Speaker.preset_musics()[0]
        mock_volume = 80
        self.speaker.play_music(mock_music, mock_volume)
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_MELODY,
            (("u8", Speaker.STATE_START), ("u8", mock_volume),
             ("string", Speaker.PRESET_MUSIC[mock_music]), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_stop_music(self):
        """Test stop_music method."""

        mock_music = Speaker.preset_musics()[0]
        mock_volume = 80
        self.speaker.play_music(mock_music, mock_volume)
        self.speaker.stop_music()
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_MELODY,
            (("u8", Speaker.STATE_STOP), ("u8", 0),
             ("string", Speaker.PRESET_MUSIC[mock_music]), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_pause_music(self):
        """Test pause_music method."""

        mock_music = Speaker.preset_musics()[0]
        mock_volume = 80
        self.speaker.play_music(mock_music, mock_volume)
        self.speaker.pause_music()
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_MELODY,
            (("u8", Speaker.STATE_PAUSE), ("u8", 0),
             ("string", Speaker.PRESET_MUSIC[mock_music]), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_resume_music(self):
        """Test resume_music method."""

        mock_music = Speaker.preset_musics()[0]
        mock_volume = 80
        self.speaker.play_music(mock_music, mock_volume)
        self.speaker.resume_music()
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_MELODY,
            (("u8", Speaker.STATE_RESUME), ("u8", 0),
             ("string", Speaker.PRESET_MUSIC[mock_music]), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)

    def test_reset(self):
        """Test reset method"""

        mock_frequency, mock_volume = 0, 0
        self.speaker.reset()
        set_message = parse_set_property_message(
            -1, Speaker.PROPERTY_SPEAKER_SET_TUNE,
            (("u16", mock_frequency), ("u16", mock_volume), )
        )
        sent_messages = []
        while self.connection.send_list:
            sent_messages.append(self.connection.send_list.pop())
        self.assertTrue(set_message in sent_messages)


if __name__ == "__main__":
    unittest.main()
