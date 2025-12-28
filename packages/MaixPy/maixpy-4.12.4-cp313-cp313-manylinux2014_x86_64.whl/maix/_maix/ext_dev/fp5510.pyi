"""
maix.ext_dev.fp5510 module
"""
from __future__ import annotations
__all__: list[str] = ['FP5510']
class FP5510:
    def __init__(self, id: int = 4, slave_addr: int = 12, freq: int = 400000) -> None:
        ...
    def get_pos(self) -> int:
        """
        Get fp5510 position
        
        Returns: returns the position of fp5510, range is [0, 1023]
        """
    def set_pos(self, pos: int) -> None:
        """
        Set fp5510 position
        
        Args:
          - pos: the position of fp5510, range is [0, 1023]
        """
