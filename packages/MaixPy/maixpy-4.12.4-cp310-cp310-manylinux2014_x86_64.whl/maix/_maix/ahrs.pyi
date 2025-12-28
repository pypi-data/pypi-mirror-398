"""
maix.ahrs module
"""
from __future__ import annotations
import maix._maix.tensor
__all__: list[str] = ['DEG2RAD', 'MahonyAHRS', 'PI', 'RAD2DEG']
class MahonyAHRS:
    ki: float
    kp: float
    def __init__(self, kp: float, ki: float) -> None:
        ...
    def get_angle(self, acc: maix._maix.tensor.Vector3f, gyro: maix._maix.tensor.Vector3f, mag: maix._maix.tensor.Vector3f, dt: float, radian: bool = False) -> maix._maix.tensor.Vector3f:
        """
        Get angle by mahony complementary filter, will automatically call update method,
        and automatically call init in first time.
        
        Args:
          - acc: accelerometer data, unit is g or raw data. maix.vector.Vector3f type.
          - gyro: gyroscope data, unit can be rad/s or degree/s, if rad/s, arg radian should be true. maix.vector.Vector3f type.
          - mag: magnetometer data, optional, if no magnetometer, set all value to 0. maix.vector.Vector3f type.
          - dt: delta T of two time call get_anle, unit is second, float type.
          - radian: if gyro's unit is rad/s, set this arg to true, degree/s set to false.
        
        
        Returns: rotation angle data, maix.vector.Vector3f type.
        """
    def init(self, ax: float, ay: float, az: float, mx: float = 0, my: float = 0, mz: float = 0) -> None:
        """
        Initialize by accelerometer and magnetometer(optional).
        If you not call this method mannually, get_angle and update method will automatically call it.
        
        Args:
          - ax: z axis of accelerometer, unit is g or raw data.
          - ay: y axis of accelerometer, unit is g or raw data.
          - mx: x axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
          - my: y axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
          - mz: z axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
        """
    def reset(self) -> None:
        """
        reset to not initialized status.
        """
    def update(self, ax: float, ay: float, az: float, gx: float, gy: float, gz: float, mx: float, my: float, mz: float, dt: float) -> None:
        """
        Update angles by accelerometer, gyroscope and magnetometer(optional).
        get_angle method will automatically call it.
        
        Args:
          - ax: z axis of gyroscope, unit is rad/s.
          - ay: y axis of gyroscope, unit is rad/s.
          - mx: x axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
          - my: y axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
          - mz: z axis of magnetometer, unit is uT or raw data, mx, my, mz all 0 means not use magnetometer.
          - dt: Delta time between two times call update method.
        """
DEG2RAD: float = 0.01745329238474369
PI: float = 3.1415927410125732
RAD2DEG: float = 57.2957763671875
