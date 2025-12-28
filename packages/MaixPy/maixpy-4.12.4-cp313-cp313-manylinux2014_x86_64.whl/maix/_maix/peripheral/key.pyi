"""
maix.peripheral.key module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['Key', 'Keys', 'State', 'add_default_listener', 'rm_default_listener']
class Key:
    def __init__(self, callback: typing.Callable[[int, int], None] = None, open: bool = True, device: str = '', long_press_time: int = 2000) -> None:
        ...
    def close(self) -> maix._maix.err.Err:
        """
        Close key device
        
        Returns: err::Err type, err.Err.ERR_NONE means success
        """
    def is_opened(self) -> bool:
        """
        Check key device is opened
        
        Returns: bool type, true means opened, false means closed
        """
    def long_press_time(self, press_time: int = -1) -> int:
        """
        Sets and retrieves the key's long press time.
        
        Args:
          - press_time: The long press time to set for the key.
        Setting it to 0 will disable the long press event.
        
        
        Returns: int type, the current long press time for the key (in milliseconds).
        """
    def open(self) -> maix._maix.err.Err:
        """
        Open(Initialize) key device, if already opened, will close first and then open.
        
        Returns: err::Err type, err.Err.ERR_NONE means success
        """
    def read(self) -> tuple[int, int]:
        """
        Read key input, and return key and value, if callback is set, DO NOT call this function manually.
        
        Returns: list type, first is key(maix.key.Keys), second is value(maix.key.State), if no key input, return [0, 0]
        """
class Keys:
    """
    Members:
    
      KEY_NONE
    
      KEY_ESC
    
      KEY_SPACE
    
      KEY_LEFT
    
      KEY_RIGHT
    
      KEY_POWER
    
      KEY_OK
    
      KEY_OPTION
    
      KEY_NEXT
    
      KEY_PREV
    """
    KEY_ESC: typing.ClassVar[Keys]  # value = <Keys.KEY_ESC: 1>
    KEY_LEFT: typing.ClassVar[Keys]  # value = <Keys.KEY_LEFT: 105>
    KEY_NEXT: typing.ClassVar[Keys]  # value = <Keys.KEY_NEXT: 407>
    KEY_NONE: typing.ClassVar[Keys]  # value = <Keys.KEY_NONE: 0>
    KEY_OK: typing.ClassVar[Keys]  # value = <Keys.KEY_OK: 352>
    KEY_OPTION: typing.ClassVar[Keys]  # value = <Keys.KEY_OPTION: 357>
    KEY_POWER: typing.ClassVar[Keys]  # value = <Keys.KEY_POWER: 116>
    KEY_PREV: typing.ClassVar[Keys]  # value = <Keys.KEY_PREV: 412>
    KEY_RIGHT: typing.ClassVar[Keys]  # value = <Keys.KEY_RIGHT: 106>
    KEY_SPACE: typing.ClassVar[Keys]  # value = <Keys.KEY_SPACE: 57>
    __members__: typing.ClassVar[dict[str, Keys]]  # value = {'KEY_NONE': <Keys.KEY_NONE: 0>, 'KEY_ESC': <Keys.KEY_ESC: 1>, 'KEY_SPACE': <Keys.KEY_SPACE: 57>, 'KEY_LEFT': <Keys.KEY_LEFT: 105>, 'KEY_RIGHT': <Keys.KEY_RIGHT: 106>, 'KEY_POWER': <Keys.KEY_POWER: 116>, 'KEY_OK': <Keys.KEY_OK: 352>, 'KEY_OPTION': <Keys.KEY_OPTION: 357>, 'KEY_NEXT': <Keys.KEY_NEXT: 407>, 'KEY_PREV': <Keys.KEY_PREV: 412>}
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
class State:
    """
    Members:
    
      KEY_RELEASED
    
      KEY_PRESSED
    
      KEY_LONG_PRESSED
    """
    KEY_LONG_PRESSED: typing.ClassVar[State]  # value = <State.KEY_LONG_PRESSED: 2>
    KEY_PRESSED: typing.ClassVar[State]  # value = <State.KEY_PRESSED: 1>
    KEY_RELEASED: typing.ClassVar[State]  # value = <State.KEY_RELEASED: 0>
    __members__: typing.ClassVar[dict[str, State]]  # value = {'KEY_RELEASED': <State.KEY_RELEASED: 0>, 'KEY_PRESSED': <State.KEY_PRESSED: 1>, 'KEY_LONG_PRESSED': <State.KEY_LONG_PRESSED: 2>}
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
def add_default_listener() -> None:
    """
    Add default listener, if you want to exit app when press ok button, you can just call this function.
    This function is auto called in MaixPy' startup code, so you don't need to call it in MaixPy.
    Create Key object will auto call rm_default_listener() to cancel the default ok button function.
    When ok button pressed, a SIGINT signal will be raise and call app.set_exit_flag(True).
    """
def rm_default_listener() -> None:
    """
    Remove default listener, if you want to cancel the default ok button function(exit app), you can just call this function.
    """
