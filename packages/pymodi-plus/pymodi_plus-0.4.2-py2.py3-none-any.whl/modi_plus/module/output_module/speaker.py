"""Speaker module."""

import time
import struct
from typing import List, Tuple, Union
from modi_plus.module.module import OutputModule


class Speaker(OutputModule):

    STATE_STOP = 0
    STATE_START = 1
    STATE_PAUSE = 2
    STATE_RESUME = 3

    PROPERTY_SPEAKER_STATE = 2

    PROPERTY_SPEAKER_SET_TUNE = 16
    PROPERTY_SPEAKER_RESET = 17
    PROPERTY_SPEAKER_MUSIC = 18
    PROPERTY_SPEAKER_MELODY = 19

    PROPERTY_OFFSET_CURRENT_VOLUME = 0
    PROPERTY_OFFSET_CURRENT_FREQUENCY = 2

    SCALE_TABLE = {
        "FA5": 698,
        "SOL5": 783,
        "LA5": 880,
        "TI5": 988,
        "DO#5": 554,
        "RE#5": 622,
        "FA#5": 739,
        "SOL#5": 830,
        "LA#5": 932,
        "DO6": 1046,
        "RE6": 1174,
        "MI6": 1318,
        "FA6": 1397,
        "SOL6": 1567,
        "LA6": 1760,
        "TI6": 1975,
        "DO#6": 1108,
        "RE#6": 1244,
        "FA#6": 1479,
        "SOL#6": 1661,
        "LA#6": 1864,
        "DO7": 2093,
        "RE7": 2349,
        "MI7": 2637
    }

    PRESET_MUSIC = {
        # .mid
        "Sylvia : Pizzicato": "res/Delibes.mid",
        "London Bridge is Falling Down": "res/London.mid",
        "Old MacDonald Had a Farm": "res/OldMac.mid",
        "Piano Concerto No.21": "res/Mozart21.mid",
        "Le Donna E mobile": "res/Verdi.mid",
        "Four Seasons: Spring": "res/Vivaldi.mid",
        "Carmen : Les Toreadors": "res/Bizet.mid",
        "The Washington Post": "res/Sousa.mid",
        "Die Forelle(The Trout)": "res/SchubeD.mid",
        "The Cuckoo Waltz": "res/Jonasson.mid",
        "Entry of the Gladiators": "res/Fucik.mid",
        "Mary had a Little Lamb": "res/Mary.mid",
        "Symphony No.9": "res/Dvorak.mid",
        "William Tell Overture": "res/Rossini.mid",
        "Symphony No.40": "res/Mozart40.mid",
        "Queen of the Night": "res/MozartQ.mid",
        "Orpheus in the Underworld": "res/BachO.mid",
        "Piano Concerto": "res/Grieg.mid",
        "Toccata and Fugue in D minor": "res/BachD.mid",
        "Symphony No. 5: I": "res/Beeth5.mid",
        "For Elise": "res/BeethF.mid",
        "Blue Danube": "res/Straus.mid",
        "Carmina Burana: O Fortuna": "res/Orff.mid",
        "Piano Concerto No.1": "res/Tchaiko1.mid",
        "Csikos Post": "res/Necke.mid",
        "Turkish March": "res/MozartR.mid",
        "Hungarian Dance No.5": "res/Brahms5.mid",
        "Dance of the Sugar Plum Fairy": "res/TchaikoD.mid",
        "Itsy Bitsy Spider": "res/Spider.mid",
        "The Farmer in The Dell": "res/Farmer.mid",
        "Liebestraum No.3(Love Dream)": "res/Liszt.mid",
        "Piano Sonata No.16": "res/Mozart16.mid",
        "Bach: Minuet in G": "res/BachG.mid",
        "Twinkle Twinkle Little Star": "res/twinkle.mid",
        "Beethoven: Minuet in G": "res/BeethG.mid",
        "Minuet": "res/Bocc.mid",
        "16 Waltzes": "res/Brahms16.mid",
        "Brahms: Lullaby": "res/BrahmsL.mid",
        "Schubert: Lullaby": "res/SchubeW.mid",
        "Yankee Doodle": "res/yankee.mid",
        "Salut d'Amour(Love's Greeting)": "res/ElgarS.mid",
        "Silver Waves": "res/Wyman.mid",
        "Waltz of the Flowers": "res/TchaikoW.mid",
        "Swan Lake : Scene": "res/TchaikoS.mid",
        "Wedding March": "res/Mendel.mid",
        "Bridal Chorus": "res/Wagner.mid",
        "Pomp and Circumstance March": "res/ElgarP.mid",
        "Happy Birthday to You": "res/Birthday.mid",
        "Jingle Bells": "res/Jingle.mid",
        "We Wish You a Merry Christmas": "res/Merry.mid",
        "Excitement": "res/Emotion1.mid",
        "Depressed": "res/Emotion2.mid",
        "Joy": "res/Emotion3.mid",
        "Warning 1": "res/Warning1.mid",
        "Warning 2": "res/Warning2.mid",
        "Start 1": "res/Start1.mid",
        "Start 2": "res/Start2.mid",
        "Complete 1": "res/Complet1.mid",
        "Complete 2": "res/Complet2.mid",

        # .wav
        "Alarm": "res/Alarm.wav",
        "Bomb": "res/Bomb.wav",
        "Camera": "res/Camera.wav",
        "Car": "res/Car.wav",
        "Complete": "res/Complete.wav",
        "Exciting": "res/Exciting.wav",
        "Robot": "res/Robot.wav",
        "Siren": "res/Siren.wav",
        "Start": "res/Start.wav",
        "Success": "res/Success.wav",
        "Win": "res/Win.wav",
        "Bouncing": "res/bouncing.wav",
    }

    @staticmethod
    def preset_notes() -> List[str]:
        return list(Speaker.SCALE_TABLE.keys())

    @staticmethod
    def preset_musics() -> List[str]:
        return list(Speaker.PRESET_MUSIC.keys())

    @property
    def tune(self) -> Tuple[int, int]:
        return self.frequency, self.volume

    @tune.setter
    def tune(self, tune_value: Tuple[Union[int, str], int]) -> None:
        """Set tune for the speaker

        :param tune_value: Value of frequency and volume
        :type tune_value: Tuple[Union[int, str], int]
        :return: None
        """

        self.set_tune(tune_value[0], tune_value[1])

    @property
    def frequency(self) -> int:
        """Returns Current frequency

        :return: Frequency value
        :rtype: int
        """

        offset = Speaker.PROPERTY_OFFSET_CURRENT_FREQUENCY
        raw = self._get_property(Speaker.PROPERTY_SPEAKER_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @frequency.setter
    def frequency(self, frequency_value: int) -> None:
        """Set the frequency for the speaker

        :param frequency_value: Frequency to set
        :type frequency_value: int
        :return: None
        """
        self.tune = frequency_value, self.volume

    @property
    def volume(self) -> int:
        """Returns Current volume

        :return: Volume value
        :rtype: int
        """

        offset = Speaker.PROPERTY_OFFSET_CURRENT_VOLUME
        raw = self._get_property(Speaker.PROPERTY_SPEAKER_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @volume.setter
    def volume(self, volume_value: int) -> None:
        """Set the volume for the speaker

        :param volume_value: Volume to set
        :type volume_value: int
        :return: None
        """
        self.tune = self.frequency, volume_value

    def set_tune(self, frequency: Union[int, str], volume: int) -> None:
        """Set tune for the speaker

        :param frequency: Frequency value
        :type frequency: int
        :param volume: Volume value
        :type volume: int
        :return: None
        """

        if isinstance(frequency, str):
            frequency = Speaker.SCALE_TABLE.get(frequency, -1)

        if frequency < 0:
            raise ValueError("Not a supported frequency value")

        self._set_property(
            destination_id=self._id,
            property_num=Speaker.PROPERTY_SPEAKER_SET_TUNE,
            property_values=(("u16", frequency), ("u16", volume), )
        )
        time.sleep(0.01)

    def play_music(self, name: str, volume: int) -> None:
        """Play music in speaker module

        :param name: Music name for playing
        :type name: str
        :param volume: Volume of speaker
        :type volume: int
        :return: None
        """

        file_name = Speaker.PRESET_MUSIC.get(name)
        if file_name is None:
            raise ValueError(f"{file_name} is not on the list, check 'Speaker.preset_musics()'")

        property_num = Speaker.PROPERTY_SPEAKER_MELODY if ".mid" in file_name else Speaker.PROPERTY_SPEAKER_MUSIC
        self.playing_file_name = file_name

        self._set_property(
            self._id,
            property_num,
            property_values=(("u8", Speaker.STATE_START),
                             ("u8", volume),
                             ("string", self.playing_file_name), )
        )
        time.sleep(0.1)

    def stop_music(self) -> None:
        """Stop music in speaker module

        :return: None
        """

        if not len(self.playing_file_name):
            return

        property_num = Speaker.PROPERTY_SPEAKER_MELODY if ".mid" in self.playing_file_name else Speaker.PROPERTY_SPEAKER_MUSIC

        self._set_property(
            self._id,
            property_num,
            property_values=(("u8", Speaker.STATE_STOP),
                             ("u8", 0),
                             ("string", self.playing_file_name), )
        )

    def pause_music(self) -> None:
        """Pause music in speaker module

        :return: None
        """

        if not len(self.playing_file_name):
            return

        property_num = Speaker.PROPERTY_SPEAKER_MELODY if ".mid" in self.playing_file_name else Speaker.PROPERTY_SPEAKER_MUSIC

        self._set_property(
            self._id,
            property_num,
            property_values=(("u8", Speaker.STATE_PAUSE),
                             ("u8", 0),
                             ("string", self.playing_file_name), )
        )

    def resume_music(self) -> None:
        """Resume music in speaker module

        :return: None
        """

        if not len(self.playing_file_name):
            return

        property_num = Speaker.PROPERTY_SPEAKER_MELODY if ".mid" in self.playing_file_name else Speaker.PROPERTY_SPEAKER_MUSIC

        self._set_property(
            self._id,
            property_num,
            property_values=(("u8", Speaker.STATE_RESUME),
                             ("u8", 0),
                             ("string", self.playing_file_name), )
        )

    def reset(self) -> None:
        """Turn off the sound

        :return: None
        """

        self.set_tune(0, 0)
