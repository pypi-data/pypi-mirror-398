"""
maix.thread module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Thread']
class Thread:
    def __init__(self, func: typing.Callable[[capsule], None], args: capsule = None) -> None:
        ...
    def detach(self) -> None:
        """
        detach thread, detach will auto start thread and you can't use join anymore.
        """
    def join(self) -> None:
        """
        wait thread exit
        """
    def joinable(self) -> bool:
        """
        Check if thread is joinable
        
        Returns: true if thread is joinable
        """
