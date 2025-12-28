"""
maix.peripheral.pinmap module
"""
from __future__ import annotations
import maix._maix.err
__all__: list[str] = ['get_pin_function', 'get_pin_functions', 'get_pins', 'set_pin_function']
def get_pin_function(pin: str) -> str:
    """
    Get pin's current function
    
    Args:
      - pin: pin name, string type.
    
    
    Returns: pin's current funtion name.
    """
def get_pin_functions(pin: str) -> list[str]:
    """
    Get all function of a pin
    
    Args:
      - pin: pin name, string type.
    
    
    Returns: function list, function name is string type.
    """
def get_pins() -> list[str]:
    """
    Get all pins of devices
    
    Returns: pin name list, string type.
    """
def set_pin_function(pin: str, func: str) -> maix._maix.err.Err:
    """
    Set function of a pin
    
    Args:
      - pin: pin name, string type.
      - func: which function should this pin use.
    
    
    Returns: if set ok, will return err.Err.ERR_NONE, else error occurs.
    """
