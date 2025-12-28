"""
maix.peripheral.hid module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['DeviceType', 'Hid']
class DeviceType:
    """
    Members:
    
      DEVICE_MOUSE
    
      DEVICE_KEYBOARD
    
      DEVICE_TOUCHPAD
    """
    DEVICE_KEYBOARD: typing.ClassVar[DeviceType]  # value = <DeviceType.DEVICE_KEYBOARD: 1>
    DEVICE_MOUSE: typing.ClassVar[DeviceType]  # value = <DeviceType.DEVICE_MOUSE: 0>
    DEVICE_TOUCHPAD: typing.ClassVar[DeviceType]  # value = <DeviceType.DEVICE_TOUCHPAD: 2>
    __members__: typing.ClassVar[dict[str, DeviceType]]  # value = {'DEVICE_MOUSE': <DeviceType.DEVICE_MOUSE: 0>, 'DEVICE_KEYBOARD': <DeviceType.DEVICE_KEYBOARD: 1>, 'DEVICE_TOUCHPAD': <DeviceType.DEVICE_TOUCHPAD: 2>}
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
class Hid:
    def __init__(self, device_type: DeviceType, open: bool = True) -> None:
        ...
    def close(self) -> maix._maix.err.Err:
        """
        Close hid device
        
        Returns: err::Err
        """
    def is_opened(self) -> bool:
        """
        Check if hid device is opened
        
        Returns: bool
        """
    def open(self) -> maix._maix.err.Err:
        """
        Open hid device
        
        Returns: err::Err
        """
    def write(self, data: list[int]) -> maix._maix.err.Err:
        """
        Write data to hid device
        
        Args:
          - data: data to write
        For the keyboard, 8 bytes of data need to be written, with the format as follows:
        data =      [0x00,   #
        0x00,   #
        0x00,   # Key value. Refer to the "Universal Serial Bus HID Usage Tables" section of the official documentation(https://www.usb.org).
        0x00,   #
        0x00,   #
        0x00,   #
        0x00,   #
        0x00]   #
        For the mouse, 4 bytes of data need to be written, with the format as follows:
        data =       [0x00,  # Button state
        0x00: no button pressed
        0x01: press left button
        0x02: press right button
        0x04: press middle button
        x,      # X-axis relative coordinates. Signed number, positive values for x indicate movement to the right
        y,      # Y-axis relative coordinates. Signed number, positive values for y indicate movement downward
        0x00]   # Wheel movement. Signed number, positive values indicate downward movement.
        For the touchpad, 6 bytes of data need to be written, with the format as follows:
        data =      [0x00,   # Button state (0: no button pressed, 0x01: press left button, 0x10, press right button.)
        x & 0xFF, (x >> 8) & 0xFF,  # X-axis absolute coordinate, 0 means unused.
        Note: You must map the target position to the range [0x1, 0x7FFF]. This means x value = <position_to_move> * 0x7FFF / <actual_screen_width>
        y & 0xFF, (y >> 8) & 0xFF,  # Y-axis absolute coordinate, 0 means unused.
        Note: You must map the target position to the range [0x1, 0x7FFF]. This means y value = <position_to_move> * 0x7FFF / <actual_screen_height>
        0x00,   # Wheel movement. Signed number, positive values indicate downward movement.
        
        
        Returns: err::Err
        """
