import os
import time

import threading as th

from textwrap import fill
from textwrap import dedent


class StoppableThread(th.Thread):

    def __init__(self, module, method):
        super(StoppableThread, self).__init__(daemon=True)
        self._stop = th.Event()
        self._module = module
        self._method = method

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        # Security: Validate method name to prevent code injection
        if not self._method.isidentifier():
            raise ValueError(f"Invalid method name: {self._method}")

        # Security: Check that the method exists before accessing it
        if not hasattr(self._module, self._method):
            raise AttributeError(f"Module has no attribute: {self._method}")

        while True:
            # Security: Use getattr() instead of eval() to prevent code injection
            prop = getattr(self._module, self._method)
            print(f"\rObtained property value: {prop} ", end="")
            time.sleep(0.1)


class Inspector:
    """
    Inspector diagnoses malfunctioning modules (all modules but network)
    """

    row_len = 79

    def __init__(self):
        self.bundle = None

    @staticmethod
    def clear():
        clear_cmd = "cls" if os.name == "nt" else "clear"
        os.system(clear_cmd)

    def print_wrap(self, msg):
        message = fill(dedent(msg), self.row_len).lstrip()
        print(message)

    def print_module_page(self, module, i, nb_modules):
        print("-" * self.row_len)
        module_to_inspect = \
            f"| {' ' * 5} Diagnosing {module.module_type} ({module.id})"
        progress_indicator = f"({i + 1} / {nb_modules}) {' ' * 5} |"
        ls = f"{module_to_inspect:<{self.row_len}}"
        s = progress_indicator.join(
            ls.rsplit(" " * len(progress_indicator), 1)
        )
        print(s)
        print("-" * self.row_len)

    def inspect(self, module, i, nb_modules):
        self.print_module_page(module, i, nb_modules)

        inspect_module = {
            # inspection method for input modules
            "battery": self.inspect_battery,

            # inspection method for input modules
            "env": self.inspect_env,
            "imu": self.inspect_imu,
            "button": self.inspect_button,
            "dial": self.inspect_dial,
            "joystick": self.inspect_joystick,
            "tof": self.inspect_tof,

            # inspection method for input modules
            "display": self.inspect_display,
            "motor": self.inspect_motor,
            "led": self.inspect_led,
            "speaker": self.inspect_speaker,
        }.get(module.module_type)
        inspect_module(module, i, nb_modules)

        self.clear()

    def inspect_battery(self, module, i, nb_modules):
        self.print_wrap(
            """
            Battery module has distance as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["level"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_env(self, module, i, nb_modules):
        self.print_wrap(
            """
            Environment module has illuminance, temperature, humidity and volume as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["illuminance", "temperature", "humidity", "volume"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_imu(self, module, i, nb_modules):
        self.print_wrap(
            """
            IMU module has angle, angular_velocity, acceleration and vibration as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["angle", "angular_velocity", "acceleration", "vibration"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_button(self, module, i, nb_modules):
        self.print_wrap(
            """
            Button module has cliked, double_clicked, pressed and toggled as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["cliked", "double_clicked", "pressed", "toggled"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_dial(self, module, i, nb_modules):
        self.print_wrap(
            """
            Dial module has turn and speed as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["turn", "speed"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_joystick(self, module, i, nb_modules):
        self.print_wrap(
            """
            Joystick module has turn and speed as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["x", "y", "direction"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_tof(self, module, i, nb_modules):
        self.print_wrap(
            """
            Tof module has distance as its property.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        properties = ["distance"]

        for prop in properties:
            self.print_module_page(module, i, nb_modules)
            print(f"If the {prop} shown below seems correct, press ENTER: \n")
            t = StoppableThread(module, prop)
            t.start()
            input()
            t.stop()

    def inspect_display(self, module, i, nb_modules):
        self.print_wrap(
            """
            Display module has a text field as its property. We wil inspect
            this property for the module.
            """
        )
        input("\nIf you are ready to inspect this module, Press ENTER: ")
        self.clear()

        self.print_module_page(module, i, nb_modules)
        module.set_text("Hello MODI+!")
        input(dedent(
            """
            We have set "Hello MODI+!" as its text, if you see this press ENTER:
            """.lstrip().rstrip() + " "
        ))
        module.reset()

    def inspect_motor(self, module, i, nb_modules):
        self.print_wrap(
            """
            Motor module has degree (i.e. position) and speed as its
            property. We will inspect position property of the module.
            """
        )
        print()
        self.print_wrap(
            """
            Before continuing, we have set motors' initial position to zero
            (your motor module may have moved a bit), so be clam :)
            """
        )
        input("\nPress ENTER to continue: ")
        self.clear()
        module.set_angle(0, 70)

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            """
            Firstly, in order to inspect position property, we have rotated 360 degree.
            """
        )
        module.set_angle(360, 70)
        time.sleep(1.5)
        input("\nIf the first motor has rotated 360 degrees, press ENTER: ")
        self.clear()

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            f"""
            It looks like the motor module ({module.id}) is properly
            functioning!
            """
        )
        input("\nTo inspect next module, press ENTER to continue: ")

    def inspect_led(self, module, i, nb_modules):
        self.print_wrap(
            """
            LED module has red, green and blue as its property. We will inspect
            these properties each.
            """
        )
        input("\nPress ENTER to continue: ")
        self.clear()

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            """
            To inspect RED, We have set LED's RED to its maximum intensity.
            """
        )
        module.set_rgb(255, 0, 0)
        input("\nIf you see strong red from the led module, Press ENTER: ")
        self.clear()

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            """
            To inspect GREEN, We have set LED's GREEN to its maximum intensity.
            """
        )
        module.set_rgb(0, 255, 0)
        input("\nIf you see strong green from the led module, Press ENTER: ")
        self.clear()

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            """
            To inspect BLUE, We have set LED's BLUE to its maximum intensity.
            """
        )
        module.set_rgb(0, 0, 255)
        input("\nIf you see strong blue from the led module, Press ENTER: ")
        self.clear()

        module.set_rgb(0, 0, 0)
        self.print_module_page(module, i, nb_modules)
        input(dedent(
            f"""
            It looks like the LED module ({module.id}) is properly functioning!
            To inspect next module, press ENTER to continue:
            """
        ))

    def inspect_speaker(self, module, i, nb_modules):
        self.print_wrap(
            """
            Speaker module has tune as its property, tune is composed of
            frequency and volume. Thus inspecting the tune property consists of
            inspecting frequency and volume properties.
            """
        )
        self.clear()

        self.print_module_page(module, i, nb_modules)
        self.print_wrap(
            """
            To inspect tune property, we have set frequency of 880 and volume
            of 50.
            """
        )
        module.set_tune(880, 50)
        input(dedent(
            "\nPress ENTER if you hear a gentle sound from the speaker module!"
        ))
        module.set_tune(880, 0)
        self.clear()

    #
    # Main methods are defined below
    #
    def run_inspection(self):
        self.clear()
        print("=" * self.row_len)
        print(f"= {'This is PyMODI+ Module Inspector':^{self.row_len - 4}} =")
        print("=" * self.row_len)

        self.print_wrap(
            """
            PyMODI+ provides a number of tools that can be utilized in different
            purpose. One of them is the module (all modules but network)
            inspector which diagnoses any malfunctioning MODI+ module.
            """
        )

        nb_modules = int(input(dedent(
            """
            Connect network module to your local machine, attach other modi+
            modules to the network module. When attaching modi+ modules, make
            sure that you provide sufficient power to the modules. Using modi+
            battery module is a good way of supplying the power to the modules.

            Type the number of modi+ modules (integer value) that are connected
            to the network module (note that the maximum number of modules is
            20) and press ENTER:
            """.rstrip() + " "
        )))
        self.clear()

        if not (1 <= nb_modules <= 20):
            print(f"ERROR: {nb_modules} is invalid for the number of modules")
            os._exit(0)

        print("Importing modi_plus package and creating a modi+ bundle object...\n")
        import modi_plus
        self.bundle = modi_plus.MODIPlus()

        input("wait for connecting.....\nif check the module connected, press ENTER\n")

        modules = [m for m in self.bundle.modules if m.module_type != "network"]
        nb_modules_detected = len(modules)
        if nb_modules != nb_modules_detected:
            self.print_wrap(
                f"""
                You said that you have attached {nb_modules} modules but PyMODI+
                detects only {nb_modules_detected} number of modules! Look at
                the printed log above regarding module connection and check
                which modules have not been printed above.
                """
            )
            os._exit(0)

        input(dedent(
            """
            It looks like all stm modules have been initialized properly! Let's
            diagnose each module, one by one!

            Press ENTER to continue:
            """.rstrip() + " "
        ))
        self.clear()

        # Let's inspect each stm module!
        for i, module in enumerate(modules):
            self.inspect(module, i, nb_modules)
