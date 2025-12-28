"""
maix.camera module, access camera device and get image from it
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.image
import typing
__all__: list[str] = ['AeMode', 'AwbMode', 'Camera', 'get_device_name', 'get_sensor_size', 'list_devices', 'set_regs_enable']
class AeMode:
    """
    Members:
    
      Invalid
    
      Auto
    
      Manual
    """
    Auto: typing.ClassVar[AeMode]  # value = <AeMode.Auto: 0>
    Invalid: typing.ClassVar[AeMode]  # value = <AeMode.Invalid: -1>
    Manual: typing.ClassVar[AeMode]  # value = <AeMode.Manual: 1>
    __members__: typing.ClassVar[dict[str, AeMode]]  # value = {'Invalid': <AeMode.Invalid: -1>, 'Auto': <AeMode.Auto: 0>, 'Manual': <AeMode.Manual: 1>}
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
class AwbMode:
    """
    Members:
    
      Invalid
    
      Auto
    
      Manual
    """
    Auto: typing.ClassVar[AwbMode]  # value = <AwbMode.Auto: 0>
    Invalid: typing.ClassVar[AwbMode]  # value = <AwbMode.Invalid: -1>
    Manual: typing.ClassVar[AwbMode]  # value = <AwbMode.Manual: 1>
    __members__: typing.ClassVar[dict[str, AwbMode]]  # value = {'Invalid': <AwbMode.Invalid: -1>, 'Auto': <AwbMode.Auto: 0>, 'Manual': <AwbMode.Manual: 1>}
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
class Camera:
    def __init__(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ..., device: str = None, fps: float = -1, buff_num: int = 3, open: bool = True, raw: bool = False) -> None:
        ...
    def add_channel(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ..., fps: float = -1, buff_num: int = 3, open: bool = True) -> Camera:
        """
        Add a new channel and return a new Camera object, you can use close() to close this channel.
        
        Args:
          - width: camera width, default is -1, means auto, mostly means max width of camera support
          - height: camera height, default is -1, means auto, mostly means max height of camera support
          - format: camera output format, default is RGB888
          - fps: camera fps, default is -1, means auto, mostly means max fps of camera support
          - buff_num: camera buffer number, default is 3, means 3 buffer, one used by user, one used for cache the next frame,
        more than one buffer will accelerate image read speed, but will cost more memory.
          - open: If true, camera will automatically call open() after creation. default is true.
        
        
        Returns: new Camera object
        """
    def awb_mode(self, value: AwbMode = ...) -> AwbMode:
        """
        Set/Get white balance mode (deprecated interface)
        
        Args:
          - value: value = 0, means set white balance to auto mode, value = 1, means set white balance to manual mode, default is auto mode.
        
        
        Returns: returns awb mode
        """
    def buff_num(self) -> int:
        """
        Get camera buffer number
        
        Returns: camera buffer number
        """
    def clear_buff(self) -> None:
        """
        Clear buff to ensure the next read image is the latest image
        """
    def close(self) -> None:
        """
        Close camera
        """
    def constrast(self, value: int = -1) -> int:
        """
        Set/Get camera constrast
        
        Args:
          - value: constrast value, range is [0, 100]
        If value == -1, returns constrast value.
        If value != 0, set and return constrast value.
        
        
        Returns: returns constrast value
        """
    def device(self) -> str:
        """
        Get camera device path
        
        Returns: camera device path
        """
    def exp_mode(self, value: AeMode = ...) -> AeMode:
        """
        Set/Get exposure mode (deprecated interface)
        
        Args:
          - value: value = 0, means set exposure to auto mode, value = 1, means set exposure to manual mode, default is auto mode.
        
        
        Returns: returns exposure mode
        """
    def exposure(self, value: int = -1) -> int:
        """
        Set/Get camera exposure
        
        Args:
          - value: exposure time. unit: us
        If value == -1, return exposure time.
        If value != 0, set and return exposure time.
        
        
        Returns: camera exposure time
        """
    def format(self) -> maix._maix.image.Format:
        """
        Get camera output format
        
        Returns: camera output format, image::Format object
        """
    def fps(self) -> float:
        """
        Get camera fps
        
        Returns: camera fps
        """
    def gain(self, value: int = -1) -> int:
        """
        Set/Get camera gain
        
        Args:
          - value: camera gain.
        If value == -1, returns camera gain.
        If value != 0, set and return camera gain.
        
        
        Returns: camera gain
        """
    def get_ch_nums(self) -> int:
        """
        Get the number of channels supported by the camera.
        
        Returns: Returns the maximum number of channels.
        """
    def get_channel(self) -> int:
        """
        Get channel of camera
        
        Returns: channel number
        """
    def get_sensor_size(self) -> list[int]:
        """
        Get sensor size
        
        Returns: Return a list of sensor sizes, the format is [w, h].
        """
    def height(self) -> int:
        """
        Get camera height
        
        Returns: camera height
        """
    def hmirror(self, value: int = -1) -> int:
        """
        Set/Get camera horizontal mirror
        
        Returns: camera horizontal mirror
        """
    def is_closed(self) -> bool:
        """
        check camera device is closed or not
        
        Returns: closed or not, bool type
        """
    def is_opened(self) -> bool:
        """
        Check if camera is opened
        
        Returns: true if camera is opened, false if not
        """
    def iso(self, value: int = -1) -> int:
        """
        Set/Get camera iso
        
        Args:
          - value: camera iso.
        If value == -1, returns camera iso.
        If value != 0, set and return camera iso.
        
        
        Returns: camera iso
        """
    def luma(self, value: int = -1) -> int:
        """
        Set/Get camera luma
        
        Args:
          - value: luma value, range is [0, 100]
        If value == -1, returns luma value.
        If value != 0, set and return luma value.
        
        
        Returns: returns luma value
        """
    def open(self, width: int = -1, height: int = -1, format: maix._maix.image.Format = ..., fps: float = -1, buff_num: int = -1) -> maix._maix.err.Err:
        """
        Open camera and run
        
        Args:
          - width: camera width, default is -1, means auto, mostly means max width of camera support
          - height: camera height, default is -1, means auto, mostly means max height of camera support
          - format: camera output format, default same as the constructor's format argument
          - fps: camera fps, default is -1, means auto, mostly means max fps of camera support
          - buff_num: camera buffer number, default is 3, means 3 buffer, one used by user, one used for cache the next frame,
        more than one buffer will accelerate image read speed, but will cost more memory.
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def read(self, block: bool = True, block_ms: int = -1) -> maix._maix.image.Image:
        """
        Get one frame image from camera buffer, must call open method before read.
        If open method not called, will call it automatically, if open failed, will throw exception!
        So call open method before read is recommended.
        
        Args:
          - block: block read, default is true, means block util read image successfully,
        if set to false, will return nullptr if no image in buffer
          - block_ms: block read timeout
        For the MaixCam, due to some issues with the platform’s interface, setting block_ms too low may result in duplicate frames being output.
        
        
        Returns: image::Image object, if failed, return nullptr, you should delete if manually in C++
        """
    def read_raw(self) -> maix._maix.image.Image:
        """
        Read the raw image and obtain the width, height, and format of the raw image through the returned Image object.
        
        Returns: image::Image object, if failed, return nullptr, you should delete if manually in C++
        """
    def read_reg(self, addr: int, bit_width: int = 8) -> int:
        """
        Read camera register
        
        Args:
          - addr: register address
          - bit_width: register data bit width, default is 8
        
        
        Returns: register data, -1 means failed
        """
    def saturation(self, value: int = -1) -> int:
        """
        Set/Get camera saturation
        
        Args:
          - value: saturation value, range is [0, 100]
        If value == -1, returns saturation value.
        If value != 0, set and return saturation value.
        
        
        Returns: returns saturation value
        """
    def set_awb(self, mode: int = -1) -> int:
        """
        Set/Get white balance mode (deprecated interface)
        
        Args:
          - value: value = 0, means set white balance to manual mode, value = 1, means set white balance to auto mode, default is auto mode.
        
        
        Returns: returns awb mode
        """
    def set_fps(self, fps: float) -> maix._maix.err.Err:
        """
        Set camera fps
        
        Args:
          - fps: new fps
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def set_resolution(self, width: int, height: int) -> maix._maix.err.Err:
        """
        Set camera resolution
        
        Args:
          - width: new width
          - height: new height
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def set_wb_gain(self, gains: list[float] = []) -> list[float]:
        """
        This interface is used to manually set the white balance gains and disable auto white balance, you can re-enable auto white balance using awb_mode().
        
        Args:
          - gains: This is a float array representing the gains for r, gr, gb, and b respectively, with a value range of 0 to 1.0.
        For MaixCam, the recommended initial values are [0.134, 0.0625, 0.0625, 0.1239]
        For MaixCam2, the recommended initial values are[0.0682, 0, 0, 0.04897]
        If no parameters are passed, the current gain values will be returned.
        
        
        Returns: Returns the current gain values.
        """
    def set_windowing(self, roi: list[int]) -> maix._maix.err.Err:
        """
        Set window size of camera
        
        Args:
          - roi: Support two input formats, [x,y,w,h] set the coordinates and size of the window;
        [w,h] set the size of the window, when the window is centred.
        
        
        Returns: error code
        """
    def show_colorbar(self, enable: bool) -> maix._maix.err.Err:
        """
        Camera output color bar image for test
        
        Args:
          - enable: enable/disable color bar
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def skip_frames(self, num: int) -> None:
        """
        Read some frames and drop, this is usually used avoid read not stable image when camera just opened.
        
        Args:
          - num: number of frames to read and drop
        """
    def vflip(self, value: int = -1) -> int:
        """
        Set/Get camera vertical flip
        
        Returns: camera vertical flip
        """
    def width(self) -> int:
        """
        Get camera width
        
        Returns: camera width
        """
    def write_reg(self, addr: int, data: int, bit_width: int = 8) -> maix._maix.err.Err:
        """
        Write camera register
        
        Args:
          - addr: register address
          - data: register data
          - bit_width: register data bit width, default is 8
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
def get_device_name() -> str:
    """
    Get device name. Most of the time, the returned name is the name of the sensor.
    """
def get_sensor_size() -> list[int]:
    """
    Get sensor size
    
    Returns: Return a list of sensor sizes, the format is [w, h].
    """
def list_devices() -> list[str]:
    """
    List all supported camera devices.
    
    Returns: Returns the path to the camera device.
    """
def set_regs_enable(enable: bool = True) -> None:
    """
    Enable set camera registers, default is false, if set to true, will not set camera registers, you can manually set registers by write_reg API.
    
    Args:
      - enable: enable/disable set camera registers
    """
