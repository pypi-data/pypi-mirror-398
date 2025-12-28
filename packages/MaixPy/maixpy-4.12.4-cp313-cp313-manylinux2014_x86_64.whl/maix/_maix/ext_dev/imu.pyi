"""
maix.ext_dev.imu module
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.tensor
import typing
__all__: list[str] = ['AccOdr', 'AccScale', 'Gcsv', 'GyroOdr', 'GyroScale', 'IMU', 'IMUData', 'IMUInfo', 'Mode', 'get_imu_info']
class AccOdr:
    """
    Members:
    
      ACC_ODR_8000
    
      ACC_ODR_4000
    
      ACC_ODR_2000
    
      ACC_ODR_1000
    
      ACC_ODR_833
    
      ACC_ODR_500
    
      ACC_ODR_416
    
      ACC_ODR_250
    
      ACC_ODR_208
    
      ACC_ODR_128
    
      ACC_ODR_125
    
      ACC_ODR_104
    
      ACC_ODR_62_5
    
      ACC_ODR_52
    
      ACC_ODR_31_25
    
      ACC_ODR_26
    
      ACC_ODR_21
    
      ACC_ODR_12_5
    
      ACC_ODR_11
    
      ACC_ODR_3
    """
    ACC_ODR_1000: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_1000: 3>
    ACC_ODR_104: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_104: 11>
    ACC_ODR_11: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_11: 18>
    ACC_ODR_125: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_125: 10>
    ACC_ODR_128: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_128: 9>
    ACC_ODR_12_5: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_12_5: 17>
    ACC_ODR_2000: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_2000: 2>
    ACC_ODR_208: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_208: 8>
    ACC_ODR_21: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_21: 16>
    ACC_ODR_250: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_250: 7>
    ACC_ODR_26: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_26: 15>
    ACC_ODR_3: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_3: 19>
    ACC_ODR_31_25: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_31_25: 14>
    ACC_ODR_4000: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_4000: 1>
    ACC_ODR_416: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_416: 6>
    ACC_ODR_500: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_500: 5>
    ACC_ODR_52: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_52: 13>
    ACC_ODR_62_5: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_62_5: 12>
    ACC_ODR_8000: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_8000: 0>
    ACC_ODR_833: typing.ClassVar[AccOdr]  # value = <AccOdr.ACC_ODR_833: 4>
    __members__: typing.ClassVar[dict[str, AccOdr]]  # value = {'ACC_ODR_8000': <AccOdr.ACC_ODR_8000: 0>, 'ACC_ODR_4000': <AccOdr.ACC_ODR_4000: 1>, 'ACC_ODR_2000': <AccOdr.ACC_ODR_2000: 2>, 'ACC_ODR_1000': <AccOdr.ACC_ODR_1000: 3>, 'ACC_ODR_833': <AccOdr.ACC_ODR_833: 4>, 'ACC_ODR_500': <AccOdr.ACC_ODR_500: 5>, 'ACC_ODR_416': <AccOdr.ACC_ODR_416: 6>, 'ACC_ODR_250': <AccOdr.ACC_ODR_250: 7>, 'ACC_ODR_208': <AccOdr.ACC_ODR_208: 8>, 'ACC_ODR_128': <AccOdr.ACC_ODR_128: 9>, 'ACC_ODR_125': <AccOdr.ACC_ODR_125: 10>, 'ACC_ODR_104': <AccOdr.ACC_ODR_104: 11>, 'ACC_ODR_62_5': <AccOdr.ACC_ODR_62_5: 12>, 'ACC_ODR_52': <AccOdr.ACC_ODR_52: 13>, 'ACC_ODR_31_25': <AccOdr.ACC_ODR_31_25: 14>, 'ACC_ODR_26': <AccOdr.ACC_ODR_26: 15>, 'ACC_ODR_21': <AccOdr.ACC_ODR_21: 16>, 'ACC_ODR_12_5': <AccOdr.ACC_ODR_12_5: 17>, 'ACC_ODR_11': <AccOdr.ACC_ODR_11: 18>, 'ACC_ODR_3': <AccOdr.ACC_ODR_3: 19>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class AccScale:
    """
    Members:
    
      ACC_SCALE_2G
    
      ACC_SCALE_4G
    
      ACC_SCALE_8G
    
      ACC_SCALE_16G
    """
    ACC_SCALE_16G: typing.ClassVar[AccScale]  # value = <AccScale.ACC_SCALE_16G: 3>
    ACC_SCALE_2G: typing.ClassVar[AccScale]  # value = <AccScale.ACC_SCALE_2G: 0>
    ACC_SCALE_4G: typing.ClassVar[AccScale]  # value = <AccScale.ACC_SCALE_4G: 1>
    ACC_SCALE_8G: typing.ClassVar[AccScale]  # value = <AccScale.ACC_SCALE_8G: 2>
    __members__: typing.ClassVar[dict[str, AccScale]]  # value = {'ACC_SCALE_2G': <AccScale.ACC_SCALE_2G: 0>, 'ACC_SCALE_4G': <AccScale.ACC_SCALE_4G: 1>, 'ACC_SCALE_8G': <AccScale.ACC_SCALE_8G: 2>, 'ACC_SCALE_16G': <AccScale.ACC_SCALE_16G: 3>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Gcsv:
    def __init__(self) -> None:
        ...
    def close(self) -> maix._maix.err.Err:
        """
        Close file
        
        Returns: error code
        """
    def is_opened(self) -> bool:
        """
        Check if the object is already open
        
        Returns: true, opened; false, not opened
        """
    def open(self, path: str, tscale: float = 0.001, gscale: float = 1, ascale: float = 1, mscale: float = 1, version: str = '1.3', id: str = 'imu', orientation: str = 'YxZ') -> maix._maix.err.Err:
        """
        Open a file
        
        Args:
          - path: the path where data will be saved
          - tscale: time scale, default is 0.001
          - gscale: gyroscope scale factor, default is 1, unit:g
          - ascale: accelerometer scale factor, default is 1, unit:radians/second
          - mscale: magnetometer scale factor, default is 1(unused)
          - version: version number, default is "1.3"
          - id: identifier for the IMU, default is "imu"
          - orientation: sensor orientation, default is "YxZ"
        
        
        Returns: error code
        """
    def write(self, timestamp: float, gyro: list[float], acc: list[float], mag: list[float] = []) -> maix._maix.err.Err:
        """
        Write imu data to gcsv file
        
        Args:
          - t: Timestamp of the current data. The actual value is equal to t * tscale. unit:s
          - gyro: Gyroscope data must be an array consisting of x, y, and z-axis data. The actual value is equal to gyro * gscale. unit:g
          - acc: Acceleration data must be an array consisting of x, y, and z-axis data. The actual value is equal to acc * ascale.unit:radians/second
          - mag: Magnetic data must be an array consisting of x, y, and z-axis data. Currently not supported.
        """
class GyroOdr:
    """
    Members:
    
      GYRO_ODR_8000
    
      GYRO_ODR_4000
    
      GYRO_ODR_2000
    
      GYRO_ODR_1000
    
      GYRO_ODR_833
    
      GYRO_ODR_500
    
      GYRO_ODR_416
    
      GYRO_ODR_250
    
      GYRO_ODR_125
    
      GYRO_ODR_208
    
      GYRO_ODR_104
    
      GYRO_ODR_62_5
    
      GYRO_ODR_52
    
      GYRO_ODR_26
    
      GYRO_ODR_31_25
    
      GYRO_ODR_12_5
    """
    GYRO_ODR_1000: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_1000: 3>
    GYRO_ODR_104: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_104: 10>
    GYRO_ODR_125: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_125: 8>
    GYRO_ODR_12_5: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_12_5: 15>
    GYRO_ODR_2000: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_2000: 2>
    GYRO_ODR_208: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_208: 9>
    GYRO_ODR_250: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_250: 7>
    GYRO_ODR_26: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_26: 13>
    GYRO_ODR_31_25: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_31_25: 14>
    GYRO_ODR_4000: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_4000: 1>
    GYRO_ODR_416: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_416: 6>
    GYRO_ODR_500: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_500: 5>
    GYRO_ODR_52: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_52: 12>
    GYRO_ODR_62_5: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_62_5: 11>
    GYRO_ODR_8000: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_8000: 0>
    GYRO_ODR_833: typing.ClassVar[GyroOdr]  # value = <GyroOdr.GYRO_ODR_833: 4>
    __members__: typing.ClassVar[dict[str, GyroOdr]]  # value = {'GYRO_ODR_8000': <GyroOdr.GYRO_ODR_8000: 0>, 'GYRO_ODR_4000': <GyroOdr.GYRO_ODR_4000: 1>, 'GYRO_ODR_2000': <GyroOdr.GYRO_ODR_2000: 2>, 'GYRO_ODR_1000': <GyroOdr.GYRO_ODR_1000: 3>, 'GYRO_ODR_833': <GyroOdr.GYRO_ODR_833: 4>, 'GYRO_ODR_500': <GyroOdr.GYRO_ODR_500: 5>, 'GYRO_ODR_416': <GyroOdr.GYRO_ODR_416: 6>, 'GYRO_ODR_250': <GyroOdr.GYRO_ODR_250: 7>, 'GYRO_ODR_125': <GyroOdr.GYRO_ODR_125: 8>, 'GYRO_ODR_208': <GyroOdr.GYRO_ODR_208: 9>, 'GYRO_ODR_104': <GyroOdr.GYRO_ODR_104: 10>, 'GYRO_ODR_62_5': <GyroOdr.GYRO_ODR_62_5: 11>, 'GYRO_ODR_52': <GyroOdr.GYRO_ODR_52: 12>, 'GYRO_ODR_26': <GyroOdr.GYRO_ODR_26: 13>, 'GYRO_ODR_31_25': <GyroOdr.GYRO_ODR_31_25: 14>, 'GYRO_ODR_12_5': <GyroOdr.GYRO_ODR_12_5: 15>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class GyroScale:
    """
    Members:
    
      GYRO_SCALE_16DPS
    
      GYRO_SCALE_32DPS
    
      GYRO_SCALE_64DPS
    
      GYRO_SCALE_125DPS
    
      GYRO_SCALE_128DPS
    
      GYRO_SCALE_250DPS
    
      GYRO_SCALE_256DPS
    
      GYRO_SCALE_500DPS
    
      GYRO_SCALE_512DPS
    
      GYRO_SCALE_1000DPS
    
      GYRO_SCALE_1024DPS
    
      GYRO_SCALE_2000DPS
    
      GYRO_SCALE_2048DPS
    """
    GYRO_SCALE_1000DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_1000DPS: 9>
    GYRO_SCALE_1024DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_1024DPS: 10>
    GYRO_SCALE_125DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_125DPS: 3>
    GYRO_SCALE_128DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_128DPS: 4>
    GYRO_SCALE_16DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_16DPS: 0>
    GYRO_SCALE_2000DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_2000DPS: 11>
    GYRO_SCALE_2048DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_2048DPS: 12>
    GYRO_SCALE_250DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_250DPS: 5>
    GYRO_SCALE_256DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_256DPS: 6>
    GYRO_SCALE_32DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_32DPS: 1>
    GYRO_SCALE_500DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_500DPS: 7>
    GYRO_SCALE_512DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_512DPS: 8>
    GYRO_SCALE_64DPS: typing.ClassVar[GyroScale]  # value = <GyroScale.GYRO_SCALE_64DPS: 2>
    __members__: typing.ClassVar[dict[str, GyroScale]]  # value = {'GYRO_SCALE_16DPS': <GyroScale.GYRO_SCALE_16DPS: 0>, 'GYRO_SCALE_32DPS': <GyroScale.GYRO_SCALE_32DPS: 1>, 'GYRO_SCALE_64DPS': <GyroScale.GYRO_SCALE_64DPS: 2>, 'GYRO_SCALE_125DPS': <GyroScale.GYRO_SCALE_125DPS: 3>, 'GYRO_SCALE_128DPS': <GyroScale.GYRO_SCALE_128DPS: 4>, 'GYRO_SCALE_250DPS': <GyroScale.GYRO_SCALE_250DPS: 5>, 'GYRO_SCALE_256DPS': <GyroScale.GYRO_SCALE_256DPS: 6>, 'GYRO_SCALE_500DPS': <GyroScale.GYRO_SCALE_500DPS: 7>, 'GYRO_SCALE_512DPS': <GyroScale.GYRO_SCALE_512DPS: 8>, 'GYRO_SCALE_1000DPS': <GyroScale.GYRO_SCALE_1000DPS: 9>, 'GYRO_SCALE_1024DPS': <GyroScale.GYRO_SCALE_1024DPS: 10>, 'GYRO_SCALE_2000DPS': <GyroScale.GYRO_SCALE_2000DPS: 11>, 'GYRO_SCALE_2048DPS': <GyroScale.GYRO_SCALE_2048DPS: 12>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class IMU:
    def __init__(self, driver: str, i2c_bus: int = -1, addr: int = 107, freq: int = 400000, mode: Mode = ..., acc_scale: AccScale = ..., acc_odr: AccOdr = ..., gyro_scale: GyroScale = ..., gyro_odr: GyroOdr = ..., block: bool = True) -> None:
        ...
    def calculate_calibration(self, time_ms: int = 30000) -> maix._maix.err.Err:
        """
        !!!Depracated!!!
        Caculate calibration, save calibration data to /maixapp/share/misc/imu_calibration
        
        Args:
          - time_ms: caculate max time, unit:ms
        
        
        Returns: err::Err
        """
    def calib_gyro(self, time_ms: int, interval_ms: int = -1, save_id: str = 'default') -> maix._maix.tensor.Vector3f:
        """
        Calibrate gryo for time_ms long, get gryo bias.
        
        Args:
          - time_ms: total time to collect data, unit is ms.
          - interval_ms: minimum read raw data interval, -1 means continues, 10ms mean >= 10ms.
          - save_id: Save calibration data to file or not, you can load by load_calib_gyro.
        Empty string means not save. By default value is "default", means save calibration as id "default".
        """
    def calib_gyro_exists(self, save_id: str = 'default') -> bool:
        """
        Load Gyro calibration from file, if not found all value will be 0.
        
        Args:
          - save_id: saved id from valib_gyro, default is "default".
        
        
        Returns: If exist gyro calibration info return True else False.
        """
    def get_calibration(self) -> list[float]:
        """
        !!!Depracated!!!
        Get calibration data
        
        Returns: return an array, format is [acc_x_bias, acc_y_bias, acc_z_bias, gyro_x_bias, gyro_y_bias, gyro_z_bias]
        If the calibration file cannot be found, an empty array will be returned.
        """
    def load_calib_gyro(self, save_id: str = 'default') -> maix._maix.tensor.Vector3f:
        """
        Load Gyro calibration from file, if not found all value will be 0.
        
        Args:
          - save_id: saved id from valib_gyro, default is "default".
        """
    def read(self) -> list[float]:
        """
        Read raw data from IMU, no calibration, recommend use read_all instead.
        
        Returns: list type. If only one of the outputs is initialized, only [x,y,z] of that output will be returned.
        If all outputs are initialized, [acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z] is returned.
        And the last one is temperature
        Unit acc: g/s
        Unit gyro: degree/s
        Unit temperate: degree
        """
    def read_all(self, calib_gryo: bool = True, radian: bool = False) -> IMUData:
        """
        read imu data from IMU.
        
        Args:
          - calib_gryo: calibrate gyro data based on calib_gyro_data, you should load_calib_gyro first to load calib_gyro_data.
          - radian: gyro unit use rad/s instead of degree/s, default false(use degree/s).
        
        
        Returns: maix.ext_dev.imu.IMUData type.
        Unit acc: g/s
        Unit gyro: degree/s
        Unit temperate: degree
        """
    def save_calib_gyro(self, calib: maix._maix.tensor.Vector3f, save_id: str = 'default') -> maix._maix.err.Err:
        """
        Save Gyro calibration to file.
        
        Args:
          - calib: the calibration data you want to save.
          - save_id: saved id from valib_gyro, default is "default".
        """
class IMUData:
    acc: maix._maix.tensor.Vector3f
    gyro: maix._maix.tensor.Vector3f
    mag: maix._maix.tensor.Vector3f
    temp: float
class IMUInfo:
    addr: int
    driver: str
    have_mag: bool
    i2c_bus: int
    name: str
class Mode:
    """
    Members:
    
      ACC_ONLY
    
      GYRO_ONLY
    
      DUAL
    """
    ACC_ONLY: typing.ClassVar[Mode]  # value = <Mode.ACC_ONLY: 0>
    DUAL: typing.ClassVar[Mode]  # value = <Mode.DUAL: 2>
    GYRO_ONLY: typing.ClassVar[Mode]  # value = <Mode.GYRO_ONLY: 1>
    __members__: typing.ClassVar[dict[str, Mode]]  # value = {'ACC_ONLY': <Mode.ACC_ONLY: 0>, 'GYRO_ONLY': <Mode.GYRO_ONLY: 1>, 'DUAL': <Mode.DUAL: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
def get_imu_info() -> list[IMUInfo]:
    """
    Get all IMU info on board(not include external IMU).
    
    Returns: std::vector<imu::IMUInfo> type, all IMU info.
    """
