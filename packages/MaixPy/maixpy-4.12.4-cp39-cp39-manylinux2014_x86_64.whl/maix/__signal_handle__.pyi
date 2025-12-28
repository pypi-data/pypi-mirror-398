from __future__ import annotations
from maix import _maix
import signal as signal
import sys as sys
import threading as threading
__all__: list[str] = ['force_exit', 'force_exit_timeout', 'register_signal_handle', 'signal', 'signal_handle', 'sys', 'threading']
def force_exit():
    ...
def register_signal_handle():
    ...
def signal_handle(signum, frame):
    ...
force_exit_timeout: int = 2
