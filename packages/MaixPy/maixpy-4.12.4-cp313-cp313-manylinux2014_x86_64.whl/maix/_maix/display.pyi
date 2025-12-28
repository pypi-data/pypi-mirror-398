"""
maix.display module, control display device and show image on it
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.image
__all__: list[str] = ['Display', 'send_to_maixvision', 'set_trans_image_quality']
class Display:
    def __init__(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ..., device: str = '', open: bool = True) -> None:
        ...
    def add_channel(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ..., open: bool = True) -> Display:
        """
        Add a new channel and return a new Display object, you can use close() to close this channel.
        
        Args:
          - width: display width, default is -1, means auto, mostly means max width of display support. Maximum width must not exceed the main channel.
          - height: display height, default is -1, means auto, mostly means max height of display support. Maximum height must not exceed the main channel.
          - format: display output format, default is FMT_BGRA8888
          - open: If true, display will automatically call open() after creation. default is true.
        
        
        Returns: new Display object
        """
    def close(self) -> maix._maix.err.Err:
        """
        close display device
        
        Returns: error code
        """
    def device(self) -> str:
        """
        Get display device path
        
        Returns: display device path
        """
    def format(self) -> maix._maix.image.Format:
        """
        Get display format
        
        Returns: format
        """
    def get_backlight(self) -> float:
        """
        Get display backlight
        
        Returns: value backlight value, float type, range is [0, 100]
        """
    def height(self) -> int:
        """
        Get display height
        
        Args:
          - ch: channel to get, by default(value is 0) means the first channel
        
        
        Returns: height
        """
    def is_closed(self) -> bool:
        """
        check display device is closed or not
        
        Returns: closed or not, bool type
        """
    def is_opened(self) -> bool:
        """
        check display device is opened or not
        
        Returns: opened or not, bool type
        """
    def is_setting_backlight(self) -> bool:
        """
        Check if backlight is in setting status
        
        Returns: true if backlight is in setting status, false if backlight is stable(on or off)
        """
    def open(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ...) -> maix._maix.err.Err:
        """
        open display device, if already opened, will return err.ERR_NONE.
        
        Args:
          - width: display width, default is -1, means auto, mostly means max width of display support
          - height: display height, default is -1, means auto, mostly means max height of display support
          - format: display output format, default is RGB888
        
        
        Returns: error code
        """
    def push(self, frame: ..., fit: maix._maix.image.Fit = ...) -> maix._maix.err.Err:
        """
        push pipeline frame to display
        
        Args:
          - frame: pipeline frame
          - fit: image in screen fit mode, by default(value is image.FIT_CONTAIN), @see image.Fit for more details
        e.g. image.FIT_CONTAIN means resize image to fit display size and keep ratio, fill blank with black color.
        
        
        Returns: error code
        """
    def set_backlight(self, value: float) -> None:
        """
        Set display backlight
        
        Args:
          - value: backlight value, float type, range is [0, 100]
        """
    def set_backlight_off(self, ms: int = 500, wait: bool = False) -> None:
        """
        Trun off display backlight in milliseconds
        
        Args:
          - ms: time in milliseconds to turn off backlight, default 500ms, 0 means immediate
          - wait: If true, will wait until the backlight is turned off before returning, or will turn off in background. Default is false.
        """
    def set_backlight_on(self, ms: int = 500, wait: bool = False) -> None:
        """
        Trun on display backlight in milliseconds
        
        Args:
          - ms: time in milliseconds to turn on backlight, default 500ms, 0 means immediate
          - wait: If true, will wait until the backlight is turned on before returning, or will turn on in background. Default is false.
        """
    def set_backlight_toggle(self, ms: int = 500, wait: bool = False) -> None:
        """
        Toggle display backlight state in milliseconds
        
        Args:
          - ms: time in milliseconds to toggle backlight, default 500ms, 0 means immediate
          - wait: If true, will wait until the backlight is turned off before returning, or will turn off in background. Default is false.
        """
    def set_hmirror(self, en: bool) -> maix._maix.err.Err:
        """
        Set display mirror
        
        Args:
          - en: enable/disable mirror
        """
    def set_vflip(self, en: bool) -> maix._maix.err.Err:
        """
        Set display flip
        
        Args:
          - en: enable/disable flip
        """
    def show(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> maix._maix.err.Err:
        """
        show image on display device, and will also send to MaixVision work station if connected.
        
        Args:
          - img: image to show, image.Image object,
        if the size of image smaller than display size, will show in the center of display;
        if the size of image bigger than display size, will auto resize to display size and keep ratio, fill blank with black color.
          - fit: image in screen fit mode, by default(value is image.FIT_CONTAIN), @see image.Fit for more details
        e.g. image.FIT_CONTAIN means resize image to fit display size and keep ratio, fill blank with black color.
        
        
        Returns: error code
        """
    def size(self) -> list[int]:
        """
        Get display size
        
        Args:
          - ch: channel to get, by default(value is 0) means the first channel
        
        
        Returns: size A list type in MaixPy, [width, height]
        """
    def width(self) -> int:
        """
        Get display width
        
        Returns: width
        """
def send_to_maixvision(img: maix._maix.image.Image) -> None:
    """
    Send image to MaixVision work station if connected.
    If you want to debug your program an don't want to initialize display, use this method.
    
    Args:
      - img: image to send, image.Image object
    """
def set_trans_image_quality(value: int) -> None:
    """
    Set image transport quality(only for JPEG)
    
    Args:
      - quality: default 95, value from 51 ~ 100
    """
