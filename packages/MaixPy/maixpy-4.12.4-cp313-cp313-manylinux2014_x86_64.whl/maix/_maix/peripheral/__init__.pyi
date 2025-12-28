"""
Chip's peripheral driver
"""
from __future__ import annotations
from . import adc
from . import gpio
from . import hid
from . import i2c
from . import key
from . import pinmap
from . import pwm
from . import spi
from . import timer
from . import uart
from . import wdt
__all__: list[str] = ['adc', 'gpio', 'hid', 'i2c', 'key', 'pinmap', 'pwm', 'spi', 'timer', 'uart', 'wdt']
