"""
maix.network module
"""
from __future__ import annotations
from . import wifi
__all__: list[str] = ['have_network', 'wifi']
def have_network() -> bool:
    """
    Return if device have network(WiFi/Eth etc.)
    
    Returns: True if have network, else False.
    """
