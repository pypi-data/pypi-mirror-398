"""
maix.peripheral.gpio module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['GPIO', 'Mode', 'Pull']
class GPIO:
    def __init__(self, pin: str, mode: Mode = ..., pull: Pull = ...) -> None:
        ...
    def get_mode(self) -> Mode:
        """
        gpio get mode
        """
    def get_pull(self) -> Pull:
        """
        get gpio pull
        
        Returns: gpio::Pull type
        """
    def high(self) -> None:
        """
        set gpio high (value to 1)
        """
    def low(self) -> None:
        """
        set gpio low (value to 0)
        """
    def reset(self, mode: Mode, pull: Pull) -> maix._maix.err.Err:
        """
        reset gpio
        
        Args:
          - mode: direction [in], gpio mode. gpio.Mode type
          - pull: direction [in], gpio pull. gpio.Pull type
        For input mode, this will set gpio default status(value), if set to gpio.Pull.PULL_NONE, gpio value will be floating.
        For output mode, this will set gpio default status(value), if set to gpio.Pull.PULL_UP, gpio value will be 1, else 0.
        
        
        Returns: err::Err type
        """
    def toggle(self) -> None:
        """
        gpio toggle
        """
    def value(self, value: int = -1) -> int:
        """
        set and get gpio value
        
        Args:
          - value: direction [in], gpio value. int type.
        0, means write gpio to low level
        1, means write gpio to high level
        -1, means read gpio value, not set
        
        
        Returns: int type, return gpio value, can be 0 or 1
        """
class Mode:
    """
    Members:
    
      IN
    
      OUT
    
      OUT_OD
    
      MODE_MAX
    """
    IN: typing.ClassVar[Mode]  # value = <Mode.IN: 1>
    MODE_MAX: typing.ClassVar[Mode]  # value = <Mode.MODE_MAX: 4>
    OUT: typing.ClassVar[Mode]  # value = <Mode.OUT: 2>
    OUT_OD: typing.ClassVar[Mode]  # value = <Mode.OUT_OD: 3>
    __members__: typing.ClassVar[dict[str, Mode]]  # value = {'IN': <Mode.IN: 1>, 'OUT': <Mode.OUT: 2>, 'OUT_OD': <Mode.OUT_OD: 3>, 'MODE_MAX': <Mode.MODE_MAX: 4>}
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
class Pull:
    """
    Members:
    
      PULL_NONE
    
      PULL_UP
    
      PULL_DOWN
    
      PULL_MAX
    """
    PULL_DOWN: typing.ClassVar[Pull]  # value = <Pull.PULL_DOWN: 2>
    PULL_MAX: typing.ClassVar[Pull]  # value = <Pull.PULL_MAX: 3>
    PULL_NONE: typing.ClassVar[Pull]  # value = <Pull.PULL_NONE: 0>
    PULL_UP: typing.ClassVar[Pull]  # value = <Pull.PULL_UP: 1>
    __members__: typing.ClassVar[dict[str, Pull]]  # value = {'PULL_NONE': <Pull.PULL_NONE: 0>, 'PULL_UP': <Pull.PULL_UP: 1>, 'PULL_DOWN': <Pull.PULL_DOWN: 2>, 'PULL_MAX': <Pull.PULL_MAX: 3>}
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
