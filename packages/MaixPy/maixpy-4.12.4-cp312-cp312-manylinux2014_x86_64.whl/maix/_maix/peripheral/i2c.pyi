"""
maix.peripheral.i2c module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['AddrSize', 'I2C', 'Mode', 'list_devices']
class AddrSize:
    """
    Members:
    
      SEVEN_BIT
    
      TEN_BIT
    """
    SEVEN_BIT: typing.ClassVar[AddrSize]  # value = <AddrSize.SEVEN_BIT: 7>
    TEN_BIT: typing.ClassVar[AddrSize]  # value = <AddrSize.TEN_BIT: 10>
    __members__: typing.ClassVar[dict[str, AddrSize]]  # value = {'SEVEN_BIT': <AddrSize.SEVEN_BIT: 7>, 'TEN_BIT': <AddrSize.TEN_BIT: 10>}
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
class I2C:
    @staticmethod
    def readfrom(*args, **kwargs):
        """
        read data from i2c slave
        
        Args:
          - addr: direction [in], i2c slave address, int type
          - len: direction [in], data length to read, int type
        
        
        Returns: the list of data read from i2c slave, bytes type, you should delete it after use in C++.
        If read failed, return nullptr in C++, None in MaixPy.
        """
    @staticmethod
    def readfrom_mem(*args, **kwargs):
        """
        read data from i2c slave
        
        Args:
          - addr: direction [in], i2c slave address, int type
          - mem_addr: direction [in], memory address want to read, int type.
          - len: direction [in], data length to read, int type
          - mem_addr_size: direction [in], memory address size, default is 8.
          - mem_addr_le: direction [in], memory address little endian, default is false, that is send high byte first.
        
        
        Returns: the list of data read from i2c slave, bytes type, you should delete it after use in C++.
        If read failed, return nullptr in C++, None in MaixPy.
        """
    def __init__(self, id: int, mode: Mode, freq: int = 100000, addr_size: AddrSize = ...) -> None:
        ...
    def scan(self, addr: int = -1) -> list[int]:
        """
        scan all i2c salve address on the bus
        
        Args:
          - addr: If -1, only scan this addr, or scan from 0x08~0x77, default -1.
        
        
        Returns: the list of i2c slave address, int list type.
        """
    def writeto(self, addr: int, data: maix.Bytes(bytes)) -> int:
        """
        write data to i2c slave
        
        Args:
          - addr: direction [in], i2c slave address, int type
          - data: direction [in], data to write, bytes type.
        Note: The range of value should be in [0,255].
        
        
        Returns: if success, return the length of written data, error occurred will return -err::Err.
        """
    def writeto_mem(self, addr: int, mem_addr: int, data: maix.Bytes(bytes), mem_addr_size: int = 8, mem_addr_le: bool = False) -> int:
        """
        write data to i2c slave's memory address
        
        Args:
          - addr: direction [in], i2c slave address, int type
          - mem_addr: direction [in], memory address want to write, int type.
          - data: direction [in], data to write, bytes type.
          - mem_addr_size: direction [in], memory address size, default is 8.
          - mem_addr_le: direction [in], memory address little endian, default is false, that is send high byte first.
        
        
        Returns: data length written if success, error occurred will return -err::Err.
        """
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
def list_devices() -> list[int]:
    """
    Get supported i2c bus devices.
    
    Returns: i2c bus devices list, int type, is the i2c bus id.
    """
