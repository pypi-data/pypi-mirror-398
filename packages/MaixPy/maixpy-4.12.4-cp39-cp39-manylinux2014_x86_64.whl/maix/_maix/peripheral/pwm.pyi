"""
maix.peripheral.pwm module
"""
from __future__ import annotations
import maix._maix.err
__all__: list[str] = ['PWM']
class PWM:
    def __init__(self, id: int, freq: int = 1000, duty: float = 0, enable: bool = True, duty_val: int = -1) -> None:
        ...
    def disable(self) -> maix._maix.err.Err:
        """
        set pwm disable
        
        Returns: err::Err type, err.Err.ERR_NONE means success
        """
    def duty(self, duty: float = -1) -> float:
        """
        get or set pwm duty
        
        Args:
          - duty: direction [in], pwm duty, double type, value in [0, 100], default -1 means only read.
        
        
        Returns: current duty, float type, if set and set failed will return -err::Err
        """
    def duty_val(self, duty_val: int = -1) -> int:
        """
        set pwm duty value
        
        Args:
          - duty_val: direction [in], pwm duty value. int type. default is -1
        duty_val > 0 means set duty_val
        duty_val == -1 or not set, return current duty_val
        
        
        Returns: int type
        when get duty_val, return current duty_val, else return -err::Err code.
        """
    def enable(self) -> maix._maix.err.Err:
        """
        set pwm enable
        
        Returns: err::Err type, err.Err.ERR_NONE means success
        """
    def freq(self, freq: int = -1) -> int:
        """
        get or set pwm frequency
        
        Args:
          - freq: direction [in], pwm frequency. int type. default is -1
        freq >= 0, set freq
        freq == -1 or not set, return current freq
        
        
        Returns: int type, current freq, if set and set failed will return -err::Err
        """
    def is_enabled(self) -> bool:
        """
        get pwm enable status
        
        Returns: bool type, true means enable, false means disable
        """
