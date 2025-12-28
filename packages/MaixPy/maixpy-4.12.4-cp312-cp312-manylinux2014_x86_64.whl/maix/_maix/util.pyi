"""
maix.util module
"""
from __future__ import annotations
__all__: list[str] = ['do_exit_function', 'init_before_main', 'register_atexit', 'str_strip']
def do_exit_function() -> None:
    """
    exec all of exit function
    """
def init_before_main() -> None:
    """
    Initialize before main
    The function is used to add preparatory operations that need to be executed before the main program runs.
    """
def register_atexit() -> None:
    """
    Registering default processes that need to be executed on exit
    """
def str_strip(s: str) -> str:
    """
    strip string, and return new striped string, will alloc new string.
    """
