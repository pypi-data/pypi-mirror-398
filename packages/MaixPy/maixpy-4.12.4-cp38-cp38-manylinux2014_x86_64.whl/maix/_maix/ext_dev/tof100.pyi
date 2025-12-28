"""
maix.ext_dev.tof100 module
"""
from __future__ import annotations
import maix._maix.ext_dev.cmap
import maix._maix.image
import typing
__all__: list[str] = ['Resolution', 'Tof100']
class Resolution:
    """
    Members:
    
      RES_100x100
    
      RES_50x50
    
      RES_25x25
    """
    RES_100x100: typing.ClassVar[Resolution]  # value = <Resolution.RES_100x100: 100>
    RES_25x25: typing.ClassVar[Resolution]  # value = <Resolution.RES_25x25: 25>
    RES_50x50: typing.ClassVar[Resolution]  # value = <Resolution.RES_50x50: 50>
    __members__: typing.ClassVar[dict[str, Resolution]]  # value = {'RES_100x100': <Resolution.RES_100x100: 100>, 'RES_50x50': <Resolution.RES_50x50: 50>, 'RES_25x25': <Resolution.RES_25x25: 25>}
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
class Tof100:
    @staticmethod
    def center_point_from(matrix: list[list[int]]) -> tuple[int, int, int]:
        """
        Finds the center pixel from the given matrix
        
        Args:
          - matrix: The distance matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the center pixel in the matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def max_dis_point_from(matrix: list[list[int]]) -> tuple[int, int, int]:
        """
        Finds the pixel with the maximum distance from the given matrix
        
        Args:
          - matrix: The distance matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the pixel with the maximum distance.
        If the operation fails, the return values will be x, y < 0.
        """
    @staticmethod
    def min_dis_point_from(matrix: list[list[int]]) -> tuple[int, int, int]:
        """
        Finds the pixel with the minimum distance from the given matrix
        
        Args:
          - matrix: The distance matrix to be analyzed.
        
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the pixel with the minimum distance.
        If the operation fails, the return values will be x, y < 0.
        """
    def __init__(self, spi_bus_num: int, resolution: Resolution = ..., cmap: maix._maix.ext_dev.cmap.Cmap = ..., dis_min: int = -1, dis_max: int = -1) -> None:
        ...
    def center_point(self) -> tuple[int, int, int]:
        """
        Finds the center pixel from the most recent reading
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the center pixel in the distance matrix.
        If the operation fails, the return values will be x, y < 0.
        """
    def image(self) -> maix._maix.image.Image:
        """
        Obtains sensor data and converts it into a pseudo-color image
        
        Returns: ::maix::image::Image* A raw pointer to a maix image object.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def image_from(self, matrix: list[list[int]]) -> maix._maix.image.Image:
        """
        Converts a given matrix of distance data into an image
        
        Args:
          - matrix: The distance matrix to be converted.
        
        
        Returns: ::maix::image::Image* A pointer to the generated image.
        It is the responsibility of the caller to free this memory
        in C/C++ to prevent memory leaks.
        """
    def matrix(self) -> list[list[int]]:
        """
        Retrieves sensor data and returns a distance matrix.
        
        Returns: Matrix containing the distance data, or an empty matrix ([]) if the operation fails.
        """
    def max_dis_point(self) -> tuple[int, int, int]:
        """
        Finds the pixel with the maximum distance from the most recent reading
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the pixel with the maximum distance.
        If the operation fails, the return values will be x, y < 0.
        """
    def min_dis_point(self) -> tuple[int, int, int]:
        """
        Finds the pixel with the minimum distance from the most recent reading
        
        Returns: Point A tuple of type <int, int, float>, representing
        (x, y, distance) of the pixel with the minimum distance.
        If the operation fails, the return values will be x, y < 0.
        """
