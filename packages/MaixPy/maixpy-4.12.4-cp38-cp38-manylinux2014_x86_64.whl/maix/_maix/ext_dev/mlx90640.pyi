"""
maix.ext_dev.mlx90640 module
"""
from __future__ import annotations
import maix._maix.ext_dev.cmap
import maix._maix.image
import typing
__all__: list[str] = ['FPS', 'MLX90640Celsius', 'MLX90640Kelvin', 'MLX_H', 'MLX_W', 'to_cmatrix', 'to_kmatrix']
class FPS:
    """
    Members:
    
      FPS_1
    
      FPS_2
    
      FPS_4
    
      FPS_8
    
      FPS_16
    
      FPS_32
    
      FPS_64
    """
    FPS_1: typing.ClassVar[FPS]  # value = <FPS.FPS_1: 1>
    FPS_16: typing.ClassVar[FPS]  # value = <FPS.FPS_16: 5>
    FPS_2: typing.ClassVar[FPS]  # value = <FPS.FPS_2: 2>
    FPS_32: typing.ClassVar[FPS]  # value = <FPS.FPS_32: 6>
    FPS_4: typing.ClassVar[FPS]  # value = <FPS.FPS_4: 3>
    FPS_64: typing.ClassVar[FPS]  # value = <FPS.FPS_64: 7>
    FPS_8: typing.ClassVar[FPS]  # value = <FPS.FPS_8: 4>
    __members__: typing.ClassVar[dict[str, FPS]]  # value = {'FPS_1': <FPS.FPS_1: 1>, 'FPS_2': <FPS.FPS_2: 2>, 'FPS_4': <FPS.FPS_4: 3>, 'FPS_8': <FPS.FPS_8: 4>, 'FPS_16': <FPS.FPS_16: 5>, 'FPS_32': <FPS.FPS_32: 6>, 'FPS_64': <FPS.FPS_64: 7>}
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
class MLX90640Celsius:
    @staticmethod
    def center_point_from(matrix: list[list[float]]) -> tuple[int, int, float]:
        """
        Finds the center pixel from the given matrix
        This static function determines the center pixel of the
        specified temperature matrix based on its dimensions.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the center pixel in the matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def max_temp_point_from(matrix: list[list[float]]) -> tuple[int, int, float]:
        """
        Finds the pixel with the maximum temperature from the given matrix
        This static function identifies the pixel with the maximum temperature
        from the specified temperature matrix.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the maximum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def min_temp_point_from(matrix: list[list[float]]) -> tuple[int, int, float]:
        """
        Finds the pixel with the minimum temperature from the given matrix
        This static function identifies the pixel with the minimum temperature
        from the specified temperature matrix.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the minimum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    def __init__(self, i2c_bus_num: int, fps: FPS = ..., cmap: maix._maix.ext_dev.cmap.Cmap = ..., temp_min: float = -1, temp_max: float = -1, emissivity: float = 0.95) -> None:
        ...
    def center_point(self) -> tuple[int, int, float]:
        """
        Finds the center pixel from the most recent reading
        This function determines the center pixel of the temperature matrix
        based on the most recent data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the center pixel in the temperature matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    def image(self) -> maix._maix.image.Image:
        """
        Obtains sensor data and converts it into a pseudo-color image
        This function retrieves the thermal data from the sensor and processes it
        to generate a pseudo-color representation of the temperature distribution.
        
        Returns: maix::image::Image* A raw pointer to a maix image object.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def image_from(self, matrix: list[list[float]]) -> maix._maix.image.Image:
        """
        Converts a given matrix of temperature data into an image
        This function takes a temperature matrix and generates
        a corresponding image representation based on the
        configured color map and other parameters.
        
        Args:
          - matrix: The temperature matrix to be converted.
        
        
        Returns: maix::image::Image* A pointer to the generated image.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def matrix(self) -> list[list[float]]:
        """
        Retrieves sensor data and returns a temperature matrix of size MLX_H * MLX_W
        MLX_W: 32
        ---------------
        |
        MLX_H  |
        : 24   |
        The matrix structure is represented as list[MLX_H][MLX_W],
        where MLX_H is the number of rows (24) and MLX_W is the number of columns (32).
        
        Returns: CMatrix containing the temperature data, or an empty matrix ([]) if the operation fails.
        """
    def max_temp_point(self) -> tuple[int, int, float]:
        """
        Finds the pixel with the maximum temperature from the most recent reading
        This function identifies the pixel with the maximum temperature
        from the latest data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the maximum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    def min_temp_point(self) -> tuple[int, int, float]:
        """
        Finds the pixel with the minimum temperature from the most recent reading
        This function identifies the pixel with the minimum temperature
        from the latest data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the minimum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
class MLX90640Kelvin:
    @staticmethod
    def center_point_from(matrix: list[list[int]]) -> tuple[int, int, float]:
        """
        Finds the center pixel from the given matrix
        This static function determines the center pixel of the
        specified temperature matrix based on its dimensions.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the center pixel in the matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def max_temp_point_from(matrix: list[list[int]]) -> tuple[int, int, float]:
        """
        Finds the pixel with the maximum temperature from the given matrix
        This static function identifies the pixel with the maximum temperature
        from the specified temperature matrix.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the maximum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def min_temp_point_from(matrix: list[list[int]]) -> tuple[int, int, float]:
        """
        Finds the pixel with the minimum temperature from the given matrix
        This static function identifies the pixel with the minimum temperature
        from the specified temperature matrix.
        
        Args:
          - matrix: The temperature matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the minimum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    def __init__(self, i2c_bus_num: int, fps: FPS = ..., cmap: maix._maix.ext_dev.cmap.Cmap = ..., temp_min: float = -1, temp_max: float = -1, emissivity: float = 0.95) -> None:
        ...
    def center_point(self) -> tuple[int, int, float]:
        """
        Finds the center pixel from the most recent reading
        This function determines the center pixel of the temperature matrix
        based on the most recent data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the center pixel in the temperature matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    def image(self) -> maix._maix.image.Image:
        """
        Obtains sensor data and converts it into a pseudo-color image
        This function retrieves the thermal data from the sensor and processes it
        to generate a pseudo-color representation of the temperature distribution.
        
        Returns: maix::image::Image* A raw pointer to a maix image object.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def image_from(self, matrix: list[list[int]]) -> maix._maix.image.Image:
        """
        Converts a given matrix of temperature data into an image
        This function takes a temperature matrix and generates
        a corresponding image representation based on the
        configured color map and other parameters.
        
        Args:
          - matrix: The temperature matrix to be converted.
        
        
        Returns: maix::image::Image* A pointer to the generated image.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def matrix(self) -> list[list[int]]:
        """
        Retrieves sensor data and returns a temperature matrix of size MLX_H * MLX_W
        MLX_W: 32
        ---------------
        |
        MLX_H  |
        : 24   |
        The matrix structure is represented as list[MLX_H][MLX_W],
        where MLX_H is the number of rows (24) and MLX_W is the number of columns (32).
        
        Returns: KMatrix containing the temperature data, or an empty matrix ([]) if the operation fails.
        """
    def max_temp_point(self) -> tuple[int, int, float]:
        """
        Finds the pixel with the minimum temperature from the most recent reading
        This function identifies the pixel with the minimum temperature
        from the latest data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the minimum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
    def min_temp_point(self) -> tuple[int, int, float]:
        """
        Finds the pixel with the maximum temperature from the most recent reading
        This function identifies the pixel with the maximum temperature
        from the latest data obtained from the sensor.
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, temperature) of the pixel with the maximum temperature.
        If the operation fails, the return values will be x, y < 0.
        """
def to_cmatrix(matrix: list[list[int]]) -> list[list[float]]:
    """
    KMatrix to CMatrix
    
    Args:
      - matrix: KMatrix type.
    
    
    Returns: CMatrix
    """
def to_kmatrix(matrix: list[list[float]]) -> list[list[int]]:
    """
    CMatrix to KMatrix.
    
    Args:
      - matrix: CMatrix type.
    
    
    Returns: KMatrix
    """
MLX_H: int = 24
MLX_W: int = 32
