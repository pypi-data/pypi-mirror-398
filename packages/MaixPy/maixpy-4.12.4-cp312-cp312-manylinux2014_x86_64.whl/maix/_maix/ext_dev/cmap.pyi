"""
maix.ext_dev.cmap module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Cmap']
class Cmap:
    """
    Members:
    
      WHITE_HOT
    
      BLACK_HOT
    
      IRONBOW
    
      NIGHT
    
      RED_HOT
    
      WHITE_HOT_SD
    
      BLACK_HOT_SD
    
      RED_HOT_SD
    
      JET
    """
    BLACK_HOT: typing.ClassVar[Cmap]  # value = <Cmap.BLACK_HOT: 1>
    BLACK_HOT_SD: typing.ClassVar[Cmap]  # value = <Cmap.BLACK_HOT_SD: 6>
    IRONBOW: typing.ClassVar[Cmap]  # value = <Cmap.IRONBOW: 2>
    JET: typing.ClassVar[Cmap]  # value = <Cmap.JET: 8>
    NIGHT: typing.ClassVar[Cmap]  # value = <Cmap.NIGHT: 3>
    RED_HOT: typing.ClassVar[Cmap]  # value = <Cmap.RED_HOT: 4>
    RED_HOT_SD: typing.ClassVar[Cmap]  # value = <Cmap.RED_HOT_SD: 7>
    WHITE_HOT: typing.ClassVar[Cmap]  # value = <Cmap.WHITE_HOT: 0>
    WHITE_HOT_SD: typing.ClassVar[Cmap]  # value = <Cmap.WHITE_HOT_SD: 5>
    __members__: typing.ClassVar[dict[str, Cmap]]  # value = {'WHITE_HOT': <Cmap.WHITE_HOT: 0>, 'BLACK_HOT': <Cmap.BLACK_HOT: 1>, 'IRONBOW': <Cmap.IRONBOW: 2>, 'NIGHT': <Cmap.NIGHT: 3>, 'RED_HOT': <Cmap.RED_HOT: 4>, 'WHITE_HOT_SD': <Cmap.WHITE_HOT_SD: 5>, 'BLACK_HOT_SD': <Cmap.BLACK_HOT_SD: 6>, 'RED_HOT_SD': <Cmap.RED_HOT_SD: 7>, 'JET': <Cmap.JET: 8>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
