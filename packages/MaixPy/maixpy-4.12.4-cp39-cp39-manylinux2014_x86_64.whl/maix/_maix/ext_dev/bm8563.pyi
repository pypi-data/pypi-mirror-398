"""
maix.ext_dev.bm8563 module
"""
from __future__ import annotations
import maix._maix.err
__all__: list[str] = ['BM8563']
class BM8563:
    def __init__(self, i2c_bus: int = -1) -> None:
        ...
    def datetime(self, timetuple: list[int] = []) -> list[int]:
        """
        Get or set the date and time of the BM8563.
        
        Args:
          - timetuple: time tuple, like (year, month, day[, hour[, minute[, second]]])
        
        
        Returns: time tuple, like (year, month, day[, hour[, minute[, second]]])
        """
    def deinit(self) -> maix._maix.err.Err:
        """
        Deinit the BM8563.
        
        Returns: err::Err err::Err type, if deinit success, return err::ERR_NONE
        """
    def hctosys(self) -> maix._maix.err.Err:
        """
        Set the system time from the BM8563
        
        Returns: err::Err type
        """
    def init(self, timetuple: list[int]) -> maix._maix.err.Err:
        """
        Initialise the BM8563.
        
        Args:
          - timetuple: time tuple, like (year, month, day[, hour[, minute[, second]]])
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def now(self) -> list[int]:
        """
        Get get the current datetime.
        
        Returns: time tuple, like (year, month, day[, hour[, minute[, second]]])
        """
    def systohc(self) -> maix._maix.err.Err:
        """
        Set the BM8563 from the system time
        
        Returns: err::Err type
        """
