"""
maix uart peripheral driver
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['BITS', 'FLOW_CTRL', 'PARITY', 'STOP', 'UART', 'list_devices']
class BITS:
    """
    Members:
    
      BITS_5
    
      BITS_6
    
      BITS_7
    
      BITS_8
    
      BITS_MAX
    """
    BITS_5: typing.ClassVar[BITS]  # value = <BITS.BITS_5: 5>
    BITS_6: typing.ClassVar[BITS]  # value = <BITS.BITS_6: 6>
    BITS_7: typing.ClassVar[BITS]  # value = <BITS.BITS_7: 7>
    BITS_8: typing.ClassVar[BITS]  # value = <BITS.BITS_8: 8>
    BITS_MAX: typing.ClassVar[BITS]  # value = <BITS.BITS_MAX: 9>
    __members__: typing.ClassVar[dict[str, BITS]]  # value = {'BITS_5': <BITS.BITS_5: 5>, 'BITS_6': <BITS.BITS_6: 6>, 'BITS_7': <BITS.BITS_7: 7>, 'BITS_8': <BITS.BITS_8: 8>, 'BITS_MAX': <BITS.BITS_MAX: 9>}
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
class FLOW_CTRL:
    """
    Members:
    
      FLOW_CTRL_NONE
    
      FLOW_CTRL_HW
    
      FLOW_CTRL_MAX
    """
    FLOW_CTRL_HW: typing.ClassVar[FLOW_CTRL]  # value = <FLOW_CTRL.FLOW_CTRL_HW: 1>
    FLOW_CTRL_MAX: typing.ClassVar[FLOW_CTRL]  # value = <FLOW_CTRL.FLOW_CTRL_MAX: 2>
    FLOW_CTRL_NONE: typing.ClassVar[FLOW_CTRL]  # value = <FLOW_CTRL.FLOW_CTRL_NONE: 0>
    __members__: typing.ClassVar[dict[str, FLOW_CTRL]]  # value = {'FLOW_CTRL_NONE': <FLOW_CTRL.FLOW_CTRL_NONE: 0>, 'FLOW_CTRL_HW': <FLOW_CTRL.FLOW_CTRL_HW: 1>, 'FLOW_CTRL_MAX': <FLOW_CTRL.FLOW_CTRL_MAX: 2>}
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
class PARITY:
    """
    Members:
    
      PARITY_NONE
    
      PARITY_ODD
    
      PARITY_EVEN
    
      PARITY_MAX
    """
    PARITY_EVEN: typing.ClassVar[PARITY]  # value = <PARITY.PARITY_EVEN: 2>
    PARITY_MAX: typing.ClassVar[PARITY]  # value = <PARITY.PARITY_MAX: 3>
    PARITY_NONE: typing.ClassVar[PARITY]  # value = <PARITY.PARITY_NONE: 0>
    PARITY_ODD: typing.ClassVar[PARITY]  # value = <PARITY.PARITY_ODD: 1>
    __members__: typing.ClassVar[dict[str, PARITY]]  # value = {'PARITY_NONE': <PARITY.PARITY_NONE: 0>, 'PARITY_ODD': <PARITY.PARITY_ODD: 1>, 'PARITY_EVEN': <PARITY.PARITY_EVEN: 2>, 'PARITY_MAX': <PARITY.PARITY_MAX: 3>}
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
class STOP:
    """
    Members:
    
      STOP_1
    
      STOP_2
    
      STOP_1_5
    
      STOP_MAX
    """
    STOP_1: typing.ClassVar[STOP]  # value = <STOP.STOP_1: 1>
    STOP_1_5: typing.ClassVar[STOP]  # value = <STOP.STOP_1_5: 3>
    STOP_2: typing.ClassVar[STOP]  # value = <STOP.STOP_2: 2>
    STOP_MAX: typing.ClassVar[STOP]  # value = <STOP.STOP_MAX: 4>
    __members__: typing.ClassVar[dict[str, STOP]]  # value = {'STOP_1': <STOP.STOP_1: 1>, 'STOP_2': <STOP.STOP_2: 2>, 'STOP_1_5': <STOP.STOP_1_5: 3>, 'STOP_MAX': <STOP.STOP_MAX: 4>}
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
class UART:
    @staticmethod
    def read(*args, **kwargs):
        """
        Recv data from uart
        
        Args:
          - len: max data length want to receive, default -1.
        -1 means read data in uart receive buffer.
        >0 means read len data want to receive.
        other values is invalid.
          - timeout: unit ms, timeout to receive data, default 0.
        0 means read data in uart receive buffer and return immediately,
        -1 means block until read len data,
        >0 means block until read len data or timeout.
        
        
        Returns: received data, bytes type.
        Attention, you need to delete the returned object yourself in C++.
        """
    @staticmethod
    def readline(*args, **kwargs):
        """
        Read line from uart, that is read until '
        ' or '
        '.
        
        Args:
          - timeout: unit ms, timeout to receive data, default -1 means block until read '
        ' or '
        '.
        > 0 means block until read '
        ' or '
        ' or timeout.
        
        
        Returns: received data, bytes type. If timeout will return the current received data despite not read '
        ' or '
        '.
        e.g. If we want to read b'123
        ', but when we only read b'12', timeout, then return b'12'.
        """
    def __init__(self, port: str = '', baudrate: int = 115200, databits: BITS = ..., parity: PARITY = ..., stopbits: STOP = ..., flow_ctrl: FLOW_CTRL = ...) -> None:
        ...
    def available(self, timeout: int = 0) -> int:
        """
        Check if data available or wait data available.
        
        Args:
          - timeout: unit ms, timeout to wait data, default 0.
        0 means check data available and return immediately,
        > 0 means wait until data available or timeout.
        - 1 means wait until data available.
        
        
        Returns: available data number, 0 if timeout or no data, <0 if error, value is -err.Err, can be err::ERR_IO， err::ERR_CANCEL, err::ERR_NOT_OPEN.
        """
    def close(self) -> maix._maix.err.Err:
        """
        Close uart device, if already closed, do nothing and return err.ERR_NONE.
        
        Returns: close device error code, err.Err type.
        """
    def get_baudrate(self) -> int:
        """
        Get baud rate
        
        Returns: baud rate, int type.
        """
    def get_port(self) -> str:
        """
        Get port
        
        Returns: uart port, string type.
        """
    def is_open(self) -> bool:
        """
        Check if device is opened.
        
        Returns: true if opened, false if not opened.
        """
    def open(self) -> maix._maix.err.Err:
        """
        Open uart device, before open, port must be set in constructor or by set_port().
        If already opened, do nothing and return err.ERR_NONE.
        
        Returns: open device error code, err.Err type.
        """
    def set_baudrate(self, baudrate: int) -> maix._maix.err.Err:
        """
        Set baud rate
        
        Args:
          - baudrate: baudrate of uart. int type, default 115200.
        
        
        Returns: set baud rate error code, err.Err type.
        """
    def set_port(self, port: str) -> maix._maix.err.Err:
        """
        Set port
        
        Args:
          - port: uart port. string type, can get it by uart.list_devices().
        
        
        Returns: set port error code, err.Err type.
        """
    def set_received_callback(self, callback: typing.Callable[[UART, maix.Bytes(bytes)], None]) -> None:
        """
        Set received callback function
        
        Args:
          - callback: function to call when received data
        """
    def write(self, data: maix.Bytes(bytes)) -> int:
        """
        Send data to uart
        
        Args:
          - data: direction [in], data to send, bytes type. If you want to send str type, use str.encode() to convert.
        
        
        Returns: sent length, int type, if < 0 means error, value is -err.Err.
        """
    def write_str(self, str: str) -> int:
        """
        Send string data
        
        Args:
          - str: string data
        
        
        Returns: sent data length, < 0 means error, value is -err.Err.
        """
def list_devices() -> list[str]:
    """
    Get supported uart ports.
    
    Returns: uart ports list, string type.
    """
