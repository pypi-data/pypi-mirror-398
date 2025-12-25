import os

from textwrap import fill
from textwrap import dedent


class UsageInstructor:
    """
    Usage Instructor teaches basic module usage of PyMODI+.
    It mainly teachs what methods are available for each module.
    """

    row_len = 79

    def __init__(self):
        self.bundle = None
        self.led = None
        self.button = None

    @staticmethod
    def clear():
        clear_cmd = "cls" if os.name == "nt" else "clear"
        os.system(clear_cmd)

    def print_wrap(self, msg):
        message = fill(dedent(msg), self.row_len).lstrip()
        print(message)

    def print_topic(self, module_type):
        print("-" * self.row_len)
        topic = f"Usage Manual {module_type}"
        print(f"{topic:^{self.row_len}}")
        print("-" * self.row_len)

    def run_usage_manual(self):
        self.clear()
        print("=" * self.row_len)
        print(f"= {'Welcome to PyMODI+ Usage Manual':^{self.row_len - 4}} =")
        print("=" * self.row_len)

        selection = dedent(
            """
            Modules available for usage:
            1. Button
            2. Dial
            3. Env
            4. Imu
            5. Joystick
            7. Tof
            8. Display
            9. Led
            10. Motor
            11. Speaker
            """
        )
        print(selection)
        module_nb = int(input(
            "Enter the module index (0 to exit) and press ENTER: "
        ))
        self.clear()

        if not (0 <= module_nb <= 11):
            print("ERROR: invalid module index")
            os._exit(0)

        run_selected_manual = {
            0: self.exit,
            1: self.run_button_manual,
            2: self.run_dial_manual,
            3: self.run_env_manual,
            4: self.run_imu_manual,
            5: self.run_joystick_manual,
            7: self.run_tof_manual,
            8: self.run_display_manual,
            9: self.run_led_manual,
            10: self.run_motor_manual,
            11: self.run_speaker_manual,
        }.get(module_nb)
        run_selected_manual()

    #
    # Usage manuals for each module
    #
    def exit(self):
        os._exit(0)

    def run_button_manual(self):
        self.print_topic("Button")

        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            button = bundle.button[0]

            while True:
                if button.clicked:
                    print(f"Button({button.id}) is clicked!")
                if button.double_clicked:
                    print(f"Button({button.id}) is double clicked!")
                if button.pressed:
                    print(f"Button({button.id}) is pressed!")
                if button.toggled:
                    print(f"Button({button.id}) is toggled!")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_dial_manual(self):
        self.print_topic("Dial")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            dial = bundle.dials[0]

            while True:
                print(f"Dial ({dial.id}) turn: {dial.turn}")
                print(f"Dial ({dial.id}) speed: {dial.speed}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_env_manual(self):
        self.print_topic("Env")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            env = bundle.envs[0]

            while True:
                print(f"Env ({env.id}) illuminance: {env.illuminance}")
                print(f"Env ({env.id}) temperature: {env.temperature}")
                print(f"Env ({env.id}) humidity: {env.humidity}")
                print(f"Env ({env.id}) volume: {env.volume}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_imu_manual(self):
        self.print_topic("Imu")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            imu = bundle.imus[0]

            while True:
                print(f"Gyro ({imu.id}) angle_x: {imu.angle_x}")
                print(f"Gyro ({imu.id}) angle_y: {imu.angle_y}")
                print(f"Gyro ({imu.id}) angle_z: {imu.angle_z}")
                print(f"Gyro ({imu.id}) angular_vel_x: {imu.angular_vel_x}")
                print(f"Gyro ({imu.id}) angular_vel_y: {imu.angular_vel_y}")
                print(f"Gyro ({imu.id}) angular_vel_z: {imu.angular_vel_z}")
                print(f"Gyro ({imu.id}) acceleration_x: {imu.acceleration_x}")
                print(f"Gyro ({imu.id}) acceleration_y: {imu.acceleration_y}")
                print(f"Gyro ({imu.id}) acceleration_z: {imu.acceleration_z}")
                print(f"Gyro ({imu.id}) vibration: {imu.vibration}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_joystick_manual(self):
        self.print_topic("Joystick")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            joystick = bundle.joysticks[0]

            while True:
                print(f"Joystick ({joystick.id}) x: {joystick.x}")
                print(f"Joystick ({joystick.id}) y: {joystick.y}")
                print(f"Joystick ({joystick.id}) direction: {joystick.direction}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_tof_manual(self):
        self.print_topic("Tof")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            tof = bundle.tofs[0]

            while True:
                print(f"ToF ({tof.id}) distance: {tof.distance}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_display_manual(self):
        self.print_topic("Display")
        print(dedent(
            """
            import modi_plus

            bundle = modi_plus.MODIPlus()
            display = bundle.displays[0]

            # Set text to display, you can check the text being displayed
            display.set_text("Hello World!")

            # Check what text has been displayed currently (in program)
            print(f"Display ({display.id}) text: {display.text})
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_led_manual(self):
        self.print_topic("Led")
        print(dedent(
            """
            import modi_plus
            import time

            bundle = modi_plus.MODIPlus()

            led = bundle.leds[0]

            # Turn the led on for a second
            led.set_rgb(100, 100, 100)
            time.sleep(1)

            # Turn the led off for a second
            led.set_rgb(0, 0, 0)
            time.sleep(1)

            # Turn red on for a second
            led.set_rgb(100, 0, 0)
            time.sleep(1)

            led.set_rgb(0, 0, 0)

            # Turn green on for a second
            led.set_rgb(0, 100, 0)
            time.sleep(1)

            led.set_rgb(0, 0, 0)

            # Turn blue on for a second
            led.set_rgb(0, 0, 100)
            time.sleep(1)

            led.set_rgb(0, 0, 0)
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_motor_manual(self):
        self.print_topic("Motor")
        print(dedent(
            """
            import modi_plus
            import time

            bundle = modi_plus.MODIPlus()
            motor = bundle.motors[0]

            motor.set_angle(0, 70)
            time.sleep(1)

            motor.set_angle(60, 70)
            time.sleep(1)

            print(f"motor ({motor.id}) angle: {motor.angle}")

            motor.set_speed(20)
            time.sleep(1)

            print(f"motor ({motor.id}) speed: {motor.speed}")
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()

    def run_speaker_manual(self):
        self.print_topic("Speaker")
        print(dedent(
            """
            import modi_plus
            import time

            bundle = modi_plus.MODIPlus()
            speaker = bundle.speakers[0]

            speaker.set_tune("SOL6", 50)
            time.sleep(1)
            """
        ))
        input("Press ENTER to exit: ")
        self.run_usage_manual()
