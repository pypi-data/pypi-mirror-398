"""
maix.peripheral.spi module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Mode', 'SPI']
class Mode:
    """
    Members:
    
      MASTER
    
      SLAVE
    """
    MASTER: typing.ClassVar[Mode]  # value = <Mode.MASTER: 0>
    SLAVE: typing.ClassVar[Mode]  # value = <Mode.SLAVE: 1>
    __members__: typing.ClassVar[dict[str, Mode]]  # value = {'MASTER': <Mode.MASTER: 0>, 'SLAVE': <Mode.SLAVE: 1>}
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
class SPI:
    @staticmethod
    def read(*args, **kwargs):
        """
        read data from spi
        
        Args:
          - length: direction [in], read length, int type
        
        
        Returns: bytes data, Bytes type in C++, bytes type in MaixPy. You need to delete it manually after use in C++.
        """
    @staticmethod
    def write_read(*args, **kwargs):
        """
        write data to spi and read data from spi at the same time.
        
        Args:
          - data: direction [in], data to write, Bytes type in C++, bytes type in MaixPy
          - read_len: direction [in], read length, int type, should > 0.
        
        
        Returns: read data, Bytes type in C++, bytes type in MaixPy. You need to delete it manually after use in C++.
        """
    def __init__(self, id: int, mode: Mode, freq: int, polarity: int = 0, phase: int = 0, bits: int = 8, hw_cs: int = -1, soft_cs: str = '', cs_active_low: bool = True) -> None:
        ...
    def is_busy(self) -> bool:
        """
        get busy status of spi
        
        Returns: busy status, bool type
        """
    def write(self, data: maix.Bytes(bytes)) -> int:
        """
        write data to spi
        
        Args:
          - data: direction [in], data to write, Bytes type in C++, bytes type in MaixPy
        
        
        Returns: write length, int type, if write failed, return -err::Err code.
        """
