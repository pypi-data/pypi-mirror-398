"""
maix.touchscreen module
"""
from __future__ import annotations
import maix._maix.err
__all__: list[str] = ['TouchScreen']
class TouchScreen:
    def __init__(self, device: str = '', open: bool = True) -> None:
        ...
    def available(self, timeout: int = 0) -> bool:
        """
        If we need to read from touchscreen, for event driven touchscreen means have event or not
        
        Args:
          - timeout: -1 means block, 0 means no block, >0 means timeout, default is 0, unit is ms.
        
        
        Returns: true if need to read(have event), false if not
        """
    def clear(self) -> None:
        """
        Clear touchscreen event buffer
        """
    def close(self) -> maix._maix.err.Err:
        """
        close touchscreen device
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def is_opened(self) -> bool:
        """
        Check if touchscreen is opened
        
        Returns: true if touchscreen is opened, false if not
        """
    def open(self) -> maix._maix.err.Err:
        """
        open touchscreen device
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def read(self) -> list[int]:
        """
        read touchscreen device
        
        Returns: Returns a list include x, y, pressed state
        """
    def read0(self) -> list[int]:
        """
        read touchscreen device
        
        Returns: Returns a list include x, y, pressed state
        """
