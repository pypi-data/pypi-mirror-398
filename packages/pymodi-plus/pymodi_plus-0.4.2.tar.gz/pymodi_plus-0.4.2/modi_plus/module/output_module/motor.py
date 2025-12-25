"""Motor module."""

import time
import struct
from typing import Tuple
from modi_plus.module.module import OutputModule


class Motor(OutputModule):

    PROPERTY_MOTOR_STATE = 2

    PROPERTY_MOTOR_SPEED = 17
    PROPERTY_MOTOR_ANGLE = 18
    PROPERTY_MOTOR_ANGLE_APPEND = 19
    PROPERTY_MOTOR_STOP = 20

    PROPERTY_OFFSET_CURRENT_ANGLE = 0
    PROPERTY_OFFSET_CURRENT_SPEED = 2
    PROPERTY_OFFSET_TARGET_ANGLE = 4
    PROPERTY_OFFSET_TARGET_SPEED = 6

    @property
    def angle(self) -> int:
        """Returns current angle

        :return: Current angle value
        :rtype: int
        """

        offset = Motor.PROPERTY_OFFSET_CURRENT_ANGLE
        raw = self._get_property(Motor.PROPERTY_MOTOR_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @angle.setter
    def angle(self, angle_value: Tuple[int, int]) -> None:
        """Sets the angle of the motor

        :param angle_value: Value of angle and speed to reach target angle
        :type angle_value: Tuple[int, int]
        :return: None
        """

        self.set_angle(angle_value[0], angle_value[1])

    @property
    def target_angle(self) -> int:
        """Returns target angle

        :return: Target angle value
        :rtype: int
        """

        offset = Motor.PROPERTY_OFFSET_TARGET_ANGLE
        raw = self._get_property(Motor.PROPERTY_MOTOR_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @property
    def speed(self) -> int:
        """Returns current speed

        :return: Current speed value
        :rtype: int
        """

        offset = Motor.PROPERTY_OFFSET_CURRENT_SPEED
        raw = self._get_property(Motor.PROPERTY_MOTOR_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    @speed.setter
    def speed(self, target_speed: int) -> None:
        """Sets the speed of the motor

        :param target_speed: Speed to set the motor.
        :type target_speed: int
        :return: None
        """

        self.set_speed(target_speed)

    @property
    def target_speed(self) -> int:
        """Returns target speed

        :return: Target speed value
        :rtype: int
        """

        offset = Motor.PROPERTY_OFFSET_TARGET_SPEED
        raw = self._get_property(Motor.PROPERTY_MOTOR_STATE)
        data = struct.unpack("H", raw[offset:offset + 2])[0]
        return data

    def set_angle(self, target_angle: int, target_speed: int = 70) -> None:
        """Sets the angle of the motor

        :param target_angle: Angle to set the motor.
        :type target_angle: int
        :param target_speed: Speed to reach target angle.
        :type target_speed: int
        :return: None
        """

        invalid_angle = (target_angle < 0 or target_angle > 360)
        invalid_speed = (target_speed < 0 or target_speed > 100)

        if invalid_angle or invalid_speed:
            return

        self._set_property(
            destination_id=self._id,
            property_num=Motor.PROPERTY_MOTOR_ANGLE,
            property_values=(("u16", target_angle),
                             ("u16", target_speed),
                             ("u16", 0),
                             ("u16", 0), )
        )
        time.sleep(0.01)

    def set_speed(self, target_speed: int) -> None:
        """Sets the speed of the motor

        :param target_speed: Speed to set the motor.
        :type target_speed: int
        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Motor.PROPERTY_MOTOR_SPEED,
            property_values=(("s32", target_speed), )
        )
        time.sleep(0.01)

    def append_angle(self, target_angle: int, target_speed: int = 70) -> None:
        """append the angle form current angle of the motor

        :param target_angle: Angle to append the motor angle.
        :type target_angle: int
        :param target_speed: Speed to reach target angle.
        :type target_speed: int
        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Motor.PROPERTY_MOTOR_ANGLE_APPEND,
            property_values=(("s16", target_angle),
                             ("u16", target_speed), ),
            force=True
        )
        time.sleep(0.01)

    def stop(self) -> None:
        """Stop operating motor

        :return: None
        """

        self._set_property(
            destination_id=self._id,
            property_num=Motor.PROPERTY_MOTOR_STOP,
            property_values=()
        )
        time.sleep(0.01)
