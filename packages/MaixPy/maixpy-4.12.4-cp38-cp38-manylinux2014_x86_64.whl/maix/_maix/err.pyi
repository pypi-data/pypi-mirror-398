"""
maix.err module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Err', 'Exception', 'check_bool_raise', 'check_null_raise', 'check_raise', 'get_error', 'set_error', 'to_str']
class Err:
    """
    Members:
    
      ERR_NONE
    
      ERR_ARGS
    
      ERR_NO_MEM
    
      ERR_NOT_IMPL
    
      ERR_NOT_READY
    
      ERR_NOT_INIT
    
      ERR_NOT_OPEN
    
      ERR_NOT_PERMIT
    
      ERR_REOPEN
    
      ERR_BUSY
    
      ERR_READ
    
      ERR_WRITE
    
      ERR_TIMEOUT
    
      ERR_RUNTIME
    
      ERR_IO
    
      ERR_NOT_FOUND
    
      ERR_ALREAY_EXIST
    
      ERR_BUFF_FULL
    
      ERR_BUFF_EMPTY
    
      ERR_CANCEL
    
      ERR_OVERFLOW
    
      ERR_MAX
    """
    ERR_ALREAY_EXIST: typing.ClassVar[Err]  # value = <Err.ERR_ALREAY_EXIST: 16>
    ERR_ARGS: typing.ClassVar[Err]  # value = <Err.ERR_ARGS: 1>
    ERR_BUFF_EMPTY: typing.ClassVar[Err]  # value = <Err.ERR_BUFF_EMPTY: 18>
    ERR_BUFF_FULL: typing.ClassVar[Err]  # value = <Err.ERR_BUFF_FULL: 17>
    ERR_BUSY: typing.ClassVar[Err]  # value = <Err.ERR_BUSY: 9>
    ERR_CANCEL: typing.ClassVar[Err]  # value = <Err.ERR_CANCEL: 19>
    ERR_IO: typing.ClassVar[Err]  # value = <Err.ERR_IO: 14>
    ERR_MAX: typing.ClassVar[Err]  # value = <Err.ERR_MAX: 21>
    ERR_NONE: typing.ClassVar[Err]  # value = <Err.ERR_NONE: 0>
    ERR_NOT_FOUND: typing.ClassVar[Err]  # value = <Err.ERR_NOT_FOUND: 15>
    ERR_NOT_IMPL: typing.ClassVar[Err]  # value = <Err.ERR_NOT_IMPL: 3>
    ERR_NOT_INIT: typing.ClassVar[Err]  # value = <Err.ERR_NOT_INIT: 5>
    ERR_NOT_OPEN: typing.ClassVar[Err]  # value = <Err.ERR_NOT_OPEN: 6>
    ERR_NOT_PERMIT: typing.ClassVar[Err]  # value = <Err.ERR_NOT_PERMIT: 7>
    ERR_NOT_READY: typing.ClassVar[Err]  # value = <Err.ERR_NOT_READY: 4>
    ERR_NO_MEM: typing.ClassVar[Err]  # value = <Err.ERR_NO_MEM: 2>
    ERR_OVERFLOW: typing.ClassVar[Err]  # value = <Err.ERR_OVERFLOW: 20>
    ERR_READ: typing.ClassVar[Err]  # value = <Err.ERR_READ: 10>
    ERR_REOPEN: typing.ClassVar[Err]  # value = <Err.ERR_REOPEN: 8>
    ERR_RUNTIME: typing.ClassVar[Err]  # value = <Err.ERR_RUNTIME: 13>
    ERR_TIMEOUT: typing.ClassVar[Err]  # value = <Err.ERR_TIMEOUT: 12>
    ERR_WRITE: typing.ClassVar[Err]  # value = <Err.ERR_WRITE: 11>
    __members__: typing.ClassVar[dict[str, Err]]  # value = {'ERR_NONE': <Err.ERR_NONE: 0>, 'ERR_ARGS': <Err.ERR_ARGS: 1>, 'ERR_NO_MEM': <Err.ERR_NO_MEM: 2>, 'ERR_NOT_IMPL': <Err.ERR_NOT_IMPL: 3>, 'ERR_NOT_READY': <Err.ERR_NOT_READY: 4>, 'ERR_NOT_INIT': <Err.ERR_NOT_INIT: 5>, 'ERR_NOT_OPEN': <Err.ERR_NOT_OPEN: 6>, 'ERR_NOT_PERMIT': <Err.ERR_NOT_PERMIT: 7>, 'ERR_REOPEN': <Err.ERR_REOPEN: 8>, 'ERR_BUSY': <Err.ERR_BUSY: 9>, 'ERR_READ': <Err.ERR_READ: 10>, 'ERR_WRITE': <Err.ERR_WRITE: 11>, 'ERR_TIMEOUT': <Err.ERR_TIMEOUT: 12>, 'ERR_RUNTIME': <Err.ERR_RUNTIME: 13>, 'ERR_IO': <Err.ERR_IO: 14>, 'ERR_NOT_FOUND': <Err.ERR_NOT_FOUND: 15>, 'ERR_ALREAY_EXIST': <Err.ERR_ALREAY_EXIST: 16>, 'ERR_BUFF_FULL': <Err.ERR_BUFF_FULL: 17>, 'ERR_BUFF_EMPTY': <Err.ERR_BUFF_EMPTY: 18>, 'ERR_CANCEL': <Err.ERR_CANCEL: 19>, 'ERR_OVERFLOW': <Err.ERR_OVERFLOW: 20>, 'ERR_MAX': <Err.ERR_MAX: 21>}
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
class Exception:
    pass
def check_bool_raise(ok: bool, msg: str = '') -> None:
    """
    Check condition, if false, raise err.Exception
    
    Args:
      - ok: direction [in], condition, if true, do nothing, if false, raise err.Exception
      - msg: direction [in], error message
    """
def check_null_raise(ptr: capsule, msg: str = '') -> None:
    """
    Check NULL pointer, if NULL, raise exception
    
    Args:
      - ptr: direction [in], pointer
      - msg: direction [in], error message
    """
def check_raise(e: Err, msg: str = '') -> None:
    """
    Check error code, if not ERR_NONE, raise err.Exception
    
    Args:
      - e: direction [in], error code, err::Err type
      - msg: direction [in], error message
    """
def get_error() -> str:
    """
    get last error string
    
    Returns: error string
    """
def set_error(str: str) -> None:
    """
    set last error string
    
    Args:
      - str: direction [in], error string
    """
def to_str(e: Err) -> str:
    """
    Error code to string
    
    Args:
      - e: direction [in], error code, err::Err type
    
    
    Returns: error string
    """
