"""
maix.log module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['LogLevel', 'get_log_level', 'get_log_use_color', 'set_log_level']
class LogLevel:
    """
    Members:
    
      LEVEL_NONE
    
      LEVEL_ERROR
    
      LEVEL_WARN
    
      LEVEL_INFO
    
      LEVEL_DEBUG
    
      LEVEL_MAX
    """
    LEVEL_DEBUG: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_DEBUG: 4>
    LEVEL_ERROR: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_ERROR: 1>
    LEVEL_INFO: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_INFO: 3>
    LEVEL_MAX: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_MAX: 5>
    LEVEL_NONE: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_NONE: 0>
    LEVEL_WARN: typing.ClassVar[LogLevel]  # value = <LogLevel.LEVEL_WARN: 2>
    __members__: typing.ClassVar[dict[str, LogLevel]]  # value = {'LEVEL_NONE': <LogLevel.LEVEL_NONE: 0>, 'LEVEL_ERROR': <LogLevel.LEVEL_ERROR: 1>, 'LEVEL_WARN': <LogLevel.LEVEL_WARN: 2>, 'LEVEL_INFO': <LogLevel.LEVEL_INFO: 3>, 'LEVEL_DEBUG': <LogLevel.LEVEL_DEBUG: 4>, 'LEVEL_MAX': <LogLevel.LEVEL_MAX: 5>}
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
def get_log_level() -> LogLevel:
    """
    Get current log level
    
    Returns: current log level
    """
def get_log_use_color() -> bool:
    """
    Get whether log use color
    
    Returns: true if log use color, else false
    """
def set_log_level(level: LogLevel, color: bool) -> None:
    """
    Set log level globally, by default log level is LEVEL_INFO.
    
    Args:
      - level: log level, @see maix.log.LogLevel
      - color: true to enable color, false to disable color
    """
