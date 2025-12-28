"""
maix.tracker module
"""
from __future__ import annotations
__all__: list[str] = ['ByteTracker', 'Object', 'Track']
class ByteTracker:
    def __init__(self, max_lost_buff_num: int = 60, track_thresh: float = 0.5, high_thresh: float = 0.6, match_thresh: float = 0.8, max_history: int = 20) -> None:
        ...
    def update(self, objs: list[...]) -> list[...]:
        """
        update tracks according to current detected objects.
        """
class Object:
    class_id: int
    h: int
    score: float
    w: int
    x: int
    y: int
    def __init__(self, x: int, y: int, w: int, h: int, class_id: int, score: float) -> None:
        ...
class Track:
    frame_id: int
    history: list[Object]
    id: int
    lost: bool
    score: float
    start_frame_id: int
    def __init__(self, id: int, score: float, lost: bool, start_frame_id: int, frame_id: int) -> None:
        ...
