"""
maix.peripheral.wdt module
"""
from __future__ import annotations
__all__: list[str] = ['WDT']
class WDT:
    def __init__(self, id: int, feed_ms: int) -> None:
        ...
    def feed(self) -> int:
        """
        feed wdt
        
        Returns: error code, if feed success, return err::ERR_NONE
        """
    def restart(self) -> int:
        """
        restart wdt, stop and start watchdog timer.
        """
    def stop(self) -> int:
        """
        stop wdt
        """
