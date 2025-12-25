"""Display module."""

import time
from typing import List
from modi_plus.module.module import OutputModule


class Display(OutputModule):

    WIDTH = 96
    HEIGHT = 96

    TEXT_SPLIT_LEN = 24
    DOT_SPLIT_LEN = 23
    DOT_LEN = int(WIDTH * HEIGHT / 8)

    PROPERTY_DISPLAY_WRITE_TEXT = 17
    PROPERTY_DISPLAY_DRAW_DOT = 18
    PROPERTY_DISPLAY_DRAW_PICTURE = 19
    PROPERTY_DISPLAY_RESET = 21
    PROPERTY_DISPLAY_WRITE_VARIABLE = 22
    PROPERTY_DISPLAY_SET_OFFSET = 25
    PROPERTY_DISPLAY_MOVE_SCREEN = 26

    PRESET_PICTURE = {
        "smiling brightly": "res/smileb.bmp",
        "falling in love": "res/love.bmp",
        "smiling": "res/smiling.bmp",
        "angry": "res/angry.bmp",
        "tired": "res/tired.bmp",
        "surprised": "res/surprise.bmp",
        "crying": "res/cry.bmp",
        "dizzy": "res/dizzy.bmp",
        "turn a blind eye": "res/bilnd.bmp",
        "sleeping": "res/sleeping.bmp",
        "embarrassed": "res/emv.bmp",
        "proud": "res/proud.bmp",
        "Devil": "res/devil.bmp",
        "Angel": "res/angel.bmp",
        "Dragon": "res/dragon.bmp",
        "Santa Claus": "res/santa.bmp",
        "Ludolf": "res/ludolf.bmp",
        "Ghost": "res/ghost.bmp",
        "Witch": "res/witch.bmp",
        "Halloween Pumpkin": "res/pumpkin.bmp",
        "magic wand": "res/wand.bmp",
        "magic hat": "res/hat.bmp",
        "crystal ball": "res/ball.bmp",
        "potion": "res/potion.bmp",
        "Dog": "res/dog.bmp",
        "Cat": "res/cat.bmp",
        "Rabbit": "res/rabbit.bmp",
        "Chick": "res/chick.bmp",
        "Lion": "res/lion.bmp",
        "Turtle": "res/turtle.bmp",
        "Sparrow": "res/sparrow.bmp",
        "Penguin": "res/penguin.bmp",
        "Butterfly": "res/butfly.bmp",
        "Fish": "res/fish.bmp",
        "Dolphin": "res/dolphin.bmp",
        "Hedgehog": "res/hedgeh.bmp",
        "Flower": "res/flower.bmp",
        "Tree": "res/tree.bmp",
        "Sun": "res/sun.bmp",
        "Star": "res/star.bmp",
        "Moon": "res/moon.bmp",
        "Earth": "res/earth.bmp",
        "Space": "res/space.bmp",
        "Cloud": "res/cloud.bmp",
        "Rain": "res/rain.bmp",
        "Snow": "res/snow.bmp",
        "Wind": "res/wind.bmp",
        "Thunder": "res/thunder.bmp",
        "Water drop": "res/water.bmp",
        "Fire": "res/fire.bmp",
        "Car": "res/car.bmp",
        "Ship": "res/ship.bmp",
        "Airplane": "res/airplane.bmp",
        "Train": "res/train.bmp",
        "Bus": "res/bus.bmp",
        "Police car": "res/policec.bmp",
        "Ambulance": "res/ambul.bmp",
        "Rocket": "res/rocket.bmp",
        "Hot-air balloon": "res/hotair.bmp",
        "Helicopter": "res/helicop.bmp",
        "Sports car": "res/sportsc.bmp",
        "Bicycle": "res/bicycle.bmp",
        "School": "res/school.bmp",
        "Park": "res/park.bmp",
        "Hospital": "res/hospital.bmp",
        "Building": "res/build.bmp",
        "Apartment": "res/apart.bmp",
        "Amusement park": "res/amuse.bmp",
        "a house of brick": "res/brick.bmp",
        "log cabin": "res/cabin.bmp",
        "a house of straw": "res/straw.bmp",
        "vacant lot": "res/vacant.bmp",
        "Field": "res/field.bmp",
        "Mountain": "res/mountain.bmp",
        "Apple": "res/apple.bmp",
        "Banana": "res/banana.bmp",
        "Strawberry": "res/strawb.bmp",
        "Peach": "res/peach.bmp",
        "Watermelon": "res/waterm.bmp",
        "Chicken": "res/chicken.bmp",
        "Pizza": "res/pizza.bmp",
        "Hamburger": "res/hamburg.bmp",
        "Cake": "res/cake.bmp",
        "Nuddle": "res/nuddle.bmp",
        "Donut": "res/donut.bmp",
        "Candy": "res/candy.bmp",
        "Communication ": "res/comm.bmp",
        "Battery": "res/battery.bmp",
        "Download": "res/download.bmp",
        "Check": "res/check.bmp",
        "X": "res/x.bmp",
        "Play": "res/play.bmp",
        "Stop": "res/stop2.bmp",
        "Pause": "res/pause.bmp",
        "Power": "res/power.bmp",
        "Bulb": "res/bulb.bmp",
        "straight sign": "res/straigh.bmp",
        "turn left sign": "res/lefts.bmp",
        "turn right sign": "res/rights.bmp",
        "stop sign": "res/stop.bmp",
        "prize": "res/prize.bmp",
        "losing ticket": "res/losing.bmp",
        "Retry": "res/retry.bmp",
        "Thumbs up": "res/thumbs.bmp",
        "Scissors": "res/scissors.bmp",
        "Rock": "res/rock.bmp",
        "Paper": "res/paper.bmp",
        "up arrow": "res/up.bmp",
        "down arrow": "res/down.bmp",
        "Right arrow": "res/righta.bmp",
        "Left arrow": "res/lefta.bmp",
        "Heart": "res/heart.bmp",
        "Musical note": "res/note.bmp",
        "baby": "res/baby.bmp",
        "Girl": "res/girl.bmp",
        "Boy": "res/boy.bmp",
        "Women": "res/women.bmp",
        "Men": "res/men.bmp",
        "Grandmother": "res/grandm.bmp",
        "Grandfather": "res/grandf.bmp",
        "Teacher": "res/teacher.bmp",
        "Programmer": "res/program.bmp",
        "Police": "res/police.bmp",
        "Doctor": "res/doctor.bmp",
        "Farmer": "res/farmer.bmp",
        "game console": "res/game.bmp",
        "Microphone": "res/microp.bmp",
        "loud speaker": "res/speaker.bmp",
        "Watch": "res/watch.bmp",
        "Telephone": "res/tele.bmp",
        "Camera": "res/camera.bmp",
        "TV": "res/tv.bmp",
        "Radio": "res/radio.bmp",
        "Book": "res/book.bmp",
        "Microscope": "res/micros.bmp",
        "Telescope": "res/teles.bmp",
        "Wastebasket": "res/waste.bmp",
        "Mask": "res/mask.bmp",
        "Flag": "res/flag.bmp",
        "Letter": "res/letter.bmp",
        "Soccer ball": "res/soccer.bmp",
        "basketball": "res/basket.bmp",
        "Piano": "res/piano.bmp",
        "Gittar": "res/gittar.bmp",
        "Drum": "res/drum.bmp",
        "Siren": "res/siren.bmp",
        "Gift box": "res/giftbox.bmp",
        "Crown": "res/crown.bmp",
        "Dice": "res/dice.bmp",
        "Medal": "res/medal.bmp",
        "Key": "res/key.bmp",
        "jewerly": "res/jewerly.bmp",
        "Coin": "res/coin.bmp",
    }

    @staticmethod
    def preset_pictures() -> List[str]:
        return list(Display.PRESET_PICTURE.keys())

    def __init__(self, id_, uuid, connection_task):
        super().__init__(id_, uuid, connection_task)
        self._text = ""

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self.write_text(text)

    def write_text(self, text: str) -> None:
        """Show the input string on the display.

        :param text: Text to display.
        :type text: str
        :return: None
        """

        n = Display.TEXT_SPLIT_LEN
        encoding_data = str.encode(str(text)) + bytes(1)
        splited_data = [encoding_data[x - n:x] for x in range(n, len(encoding_data) + n, n)]
        for index, data in enumerate(splited_data):
            self._set_property(
                self._id,
                Display.PROPERTY_DISPLAY_WRITE_TEXT,
                property_values=(("bytes", data), ),
                force=True
            )

        self._text = text
        time.sleep(0.02 + 0.003 * len(encoding_data))

    def write_variable_xy(self, x: int, y: int, variable: float) -> None:
        """Show the input variable on the display.

        :param x: X coordinate of the desired position
        :type x: int
        :param y: Y coordinate of te desired position
        :type y: int
        :param variable: Variable to display.
        :type variable: float
        :return: None
        """
        self._set_property(
            self._id,
            Display.PROPERTY_DISPLAY_WRITE_VARIABLE,
            property_values=(("u8", x),
                             ("u8", y),
                             ("float", variable), )
        )
        self._text += str(variable)
        time.sleep(0.01)

    def write_variable_line(self, line: int, variable: float) -> None:
        """Show the input variable on the display.

        :param line: display line number of the desired position
        :type line: int
        :param variable: Variable to display.
        :type variable: float
        :return: None
        """
        self._set_property(
            self._id,
            Display.PROPERTY_DISPLAY_WRITE_VARIABLE,
            property_values=(("u8", 0),
                             ("u8", line * 20),
                             ("float", variable), )
        )
        self._text += str(variable)
        time.sleep(0.01)

    def draw_picture(self, name: int) -> None:
        """Clears the display and show the input picture on the display.

        :param x: X coordinate of the desired position
        :type x: int
        :param y: Y coordinate of te desired position
        :type y: int
        :param name: Picture name to display.
        :type name: float
        :return: None
        """

        file_name = Display.PRESET_PICTURE.get(name)
        if file_name is None:
            raise ValueError(f"{file_name} is not on the list, check 'Display.preset_pictures()'")

        self._set_property(
            self._id,
            Display.PROPERTY_DISPLAY_DRAW_PICTURE,
            property_values=(("u8", 0),
                             ("u8", 0),
                             ("u8", Display.WIDTH),
                             ("u8", Display.HEIGHT),
                             ("string", file_name), )
        )
        time.sleep(0.05)

    def draw_dot(self, dot: bytes) -> None:
        """Clears the display and show the input dot on the display.

        :param dot: Dot to display
        :type dot: bytes
        :return: None
        """

        if not isinstance(dot, bytes):
            raise ValueError("dot type must bytes")

        if len(dot) != Display.DOT_LEN:
            raise ValueError(f"dot length must be {Display.DOT_LEN}")

        n = Display.DOT_SPLIT_LEN
        splited_data = [dot[x - n:x] for x in range(n, len(dot) + n, n)]
        for index, data in enumerate(splited_data):
            send_data = bytes([index]) + data

            self._set_property(
                self._id,
                Display.PROPERTY_DISPLAY_DRAW_DOT,
                property_values=(("bytes", send_data), )
            )
        time.sleep(0.3)

    def set_offset(self, x: int, y: int) -> None:
        """Set origin point on the screen

        :param x: X-axis offset on screen
        :type x: int
        :param y: Y-axis offset on screen
        :type y: int
        :return: None
        """

        self._set_property(
            self.id,
            Display.PROPERTY_DISPLAY_SET_OFFSET,
            property_values=(("s8", x), ("s8", y), )
        )
        time.sleep(0.01)

    def reset(self, mode=0) -> None:
        """Clear the screen.

        :param mode: Erase mode
            - mode 0 : Erase inside buffer(it looks like nothing has changed)
            - mode 1 : Erase display
        :return: None
        """

        if mode > 1:
            mode = 0

        self._set_property(
            self._id,
            Display.PROPERTY_DISPLAY_RESET,
            property_values=(("u8", mode), )
        )
        self._text = ""
        time.sleep(0.01)
