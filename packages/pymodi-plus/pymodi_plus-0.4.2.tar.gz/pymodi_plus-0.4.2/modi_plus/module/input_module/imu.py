"""Imu module."""

import struct
from typing import Tuple
from modi_plus.module.module import InputModule


class Imu(InputModule):

    PROPERTY_ANGLE_STATE = 2
    PROPERTY_ACC_STATE = 3
    PROPERTY_GYRO_STATE = 4
    PROPERTY_VIBRATION_STATE = 5

    PROPERTY_OFFSET_ROLL = 0
    PROPERTY_OFFSET_PITCH = 4
    PROPERTY_OFFSET_YAW = 8
    PROPERTY_OFFSET_ACC_X = 0
    PROPERTY_OFFSET_ACC_Y = 4
    PROPERTY_OFFSET_ACC_Z = 8
    PROPERTY_OFFSET_GYRO_X = 0
    PROPERTY_OFFSET_GYRO_Y = 4
    PROPERTY_OFFSET_GYRO_Z = 8
    PROPERTY_OFFSET_VIBRATION = 0

    @property
    def angle_x(self) -> float:
        """Returns the angle_x angle of the imu

        :return: The imu's angle_x angle.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_ROLL
        raw = self._get_property(Imu.PROPERTY_ANGLE_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angle_y(self) -> float:
        """Returns the angle_y angle of the imu

        :return: The imu's angle_y angle.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_PITCH
        raw = self._get_property(Imu.PROPERTY_ANGLE_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angle_z(self) -> float:
        """Returns the angle_zle_z angle of the imu

        :return: The imu's angle_z angle.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_YAW
        raw = self._get_property(Imu.PROPERTY_ANGLE_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angle(self) -> Tuple[float, float, float]:
        """Returns the angle_x, angle_y and angle_z angle of the imu

        :return: The imu's angles of angle_x, angle_y and angle_z.
        :rtype: tuple
        """

        return self.angle_x, self.angle_y, self.angle_z

    @property
    def angular_vel_x(self) -> float:
        """Returns the angle_x angle of the imu

        :return: The imu's angular velocity the about x-axis.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_GYRO_X
        raw = self._get_property(Imu.PROPERTY_GYRO_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angular_vel_y(self) -> float:
        """Returns the angular velocity about y-axis

        :return: The imu's angular velocity the about y-axis.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_GYRO_Y
        raw = self._get_property(Imu.PROPERTY_GYRO_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angular_vel_z(self) -> float:
        """Returns the angular velocity about z-axis

        :return: The imu's angular velocity the about z-axis.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_GYRO_Z
        raw = self._get_property(Imu.PROPERTY_GYRO_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def angular_velocity(self) -> Tuple[float, float, float]:
        """Returns the angular velocity about x, y and z axis

        :return: The imu's angular velocity the about x, y and z axis.
        :rtype: tuple
        """

        return self.angular_vel_x, self.angular_vel_y, self.angular_vel_z

    @property
    def acceleration_x(self) -> float:
        """Returns the x component of the acceleration

        :return: The imu's x-axis acceleration.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_ACC_X
        raw = self._get_property(Imu.PROPERTY_ACC_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def acceleration_y(self) -> float:
        """Returns the y component of the acceleration

        :return: The imu's y-axis acceleration.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_ACC_Y
        raw = self._get_property(Imu.PROPERTY_ACC_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def acceleration_z(self) -> float:
        """Returns the z component of the acceleration

        :return: The imu's z-axis acceleration.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_ACC_Z
        raw = self._get_property(Imu.PROPERTY_ACC_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """Returns the acceleration about x, y and z axis

        :return: The imu's acceleration the about x, y and z axis.
        :rtype: tuple
        """

        return self.acceleration_x, self.acceleration_y, self.acceleration_z

    @property
    def vibration(self) -> float:
        """Returns the vibration value

        :return: The imu's vibration.
        :rtype: float
        """

        offset = Imu.PROPERTY_OFFSET_VIBRATION
        raw = self._get_property(Imu.PROPERTY_VIBRATION_STATE)
        data = struct.unpack("f", raw[offset:offset + 4])[0]
        return data
