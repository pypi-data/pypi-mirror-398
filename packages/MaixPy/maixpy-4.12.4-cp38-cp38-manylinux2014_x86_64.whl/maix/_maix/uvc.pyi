"""
maix.uvc module
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.image
import typing
__all__: list[str] = ['UvcServer', 'UvcStreamer', 'helper_fill_mjpg_image']
class UvcServer:
    def __init__(self, cb: typing.Callable[[capsule, int], int] = None) -> None:
        ...
    def run(self) -> None:
        """
        run UvcServer
        
        Returns: void
        """
    def set_cb(self, cb: typing.Callable[[capsule, int], int]) -> None:
        """
        set UvcServer's cb
        
        Args:
          - cb: callback function
        
        
        Returns: void
        """
    def stop(self) -> None:
        """
        stop UvcServer
        
        Returns: void
        """
class UvcStreamer:
    def __init__(self) -> None:
        ...
    def show(self, img: maix._maix.image.Image) -> maix._maix.err.Err:
        """
        Write data to uvc
        
        Args:
          - img: image object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def use_mjpg(self, b: int = 1) -> None:
        """
        use mjpg on uvc
        
        Args:
          - b: using mjpg: 0 for NOT, others to use
        
        
        Returns: void
        """
def helper_fill_mjpg_image(buf: capsule, size: int, img: maix._maix.image.Image) -> int:
    """
    helper_fill_mjpg_image
    
    Args:
      - buf: to be filled
      - size: to be set
      - img: image::Image
    
    
    Returns: int
    """
