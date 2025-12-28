"""
maix.peripheral.adc module
"""
from __future__ import annotations
__all__: list[str] = ['ADC', 'RES_BIT_10', 'RES_BIT_12', 'RES_BIT_16', 'RES_BIT_8']
class ADC:
    def __init__(self, id: int, resolution: int, vref: float = -1) -> None:
        ...
    def read(self) -> int:
        """
        read adc value
        
        Returns: adc data, int type
        if resolution is 8-bit, return value range is [0, 255]
        if resolution is 10-bit, return value range is [0, 1023]
        if resolution is 12-bit, return value range is [0, 4095]
        if resolution is 16-bit, return value range is [0, 65535]
        """
    def read_vol(self) -> float:
        """
        read adc voltage
        
        Returns: adc voltage, float type。the range is [0.0, vref]
        """
RES_BIT_10: int = 10
RES_BIT_12: int = 12
RES_BIT_16: int = 16
RES_BIT_8: int = 8
