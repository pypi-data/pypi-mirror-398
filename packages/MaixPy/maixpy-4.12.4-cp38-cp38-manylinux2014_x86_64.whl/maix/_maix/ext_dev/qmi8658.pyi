"""
maix.ext_dev.qmi8658 module
"""
from __future__ import annotations
import maix._maix.ext_dev.imu
__all__: list[str] = ['QMI8658']
class QMI8658:
    def __init__(self, i2c_bus: int = -1, addr: int = 107, freq: int = 400000, mode: maix._maix.ext_dev.imu.Mode = ..., acc_scale: maix._maix.ext_dev.imu.AccScale = ..., acc_odr: maix._maix.ext_dev.imu.AccOdr = ..., gyro_scale: maix._maix.ext_dev.imu.GyroScale = ..., gyro_odr: maix._maix.ext_dev.imu.GyroOdr = ..., block: bool = True) -> None:
        ...
    def read(self) -> list[float]:
        """
        Read data from QMI8658.
        
        Returns: list type. If only one of the outputs is initialized, only [x,y,z] of that output will be returned.
        If all outputs are initialized, [acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z] is returned.
        """
