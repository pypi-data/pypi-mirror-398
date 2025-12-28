"""
maix.rtsp module
"""
from __future__ import annotations
import maix._maix.audio
import maix._maix.camera
import maix._maix.err
import maix._maix.image
import maix._maix.video
import typing
__all__: list[str] = ['Region', 'Rtsp', 'RtspStreamType']
class Region:
    def __init__(self, x: int, y: int, width: int, height: int, format: maix._maix.image.Format, camera: maix._maix.camera.Camera) -> None:
        ...
    def get_canvas(self) -> maix._maix.image.Image:
        """
        Return an image object from region
        
        Returns: image object
        """
    def update_canvas(self) -> maix._maix.err.Err:
        """
        Update canvas
        
        Returns: error code
        """
class Rtsp:
    def __init__(self, ip: str = '', port: int = 8554, fps: int = 30, stream_type: RtspStreamType = ..., bitrate: int = 3000000) -> None:
        ...
    def add_region(self, x: int, y: int, width: int, height: int, format: maix._maix.image.Format = ...) -> Region:
        """
        return a region object, you can draw image on the region.(This function will be removed in the future)
        
        Args:
          - x: region coordinate x
          - y: region coordinate y
          - width: region width
          - height: region height
          - format: region format, support Format::FMT_BGRA8888 only
        
        
        Returns: the reigon object
        """
    def bind_audio_recorder(self, recorder: maix._maix.audio.Recorder) -> maix._maix.err.Err:
        """
        Bind audio recorder
        
        Args:
          - recorder: audio_recorder object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def bind_camera(self, camera: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind camera
        
        Args:
          - camera: camera object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def del_region(self, region: Region) -> maix._maix.err.Err:
        """
        del region(This function will be removed in the future)
        
        Returns: error code
        """
    def draw_rect(self, id: int, x: int, y: int, width: int, height: int, color: maix._maix.image.Color, thickness: int = 1) -> maix._maix.err.Err:
        """
        Draw a rectangle on the canvas(This function will be removed in the future)
        
        Args:
          - id: region id
          - x: rectangle coordinate x
          - y: rectangle coordinate y
          - width: rectangle width
          - height: rectangle height
          - color: rectangle color
          - thickness: rectangle thickness. If you set it to -1, the rectangle will be filled.
        
        
        Returns: error code
        """
    def draw_string(self, id: int, x: int, y: int, str: str, color: maix._maix.image.Color, size: int = 16, thickness: int = 1) -> maix._maix.err.Err:
        """
        Draw a string on the canvas(This function will be removed in the future)
        
        Args:
          - id: region id
          - x: string coordinate x
          - y: string coordinate y
          - str: string
          - color: string color
          - size: string size
          - thickness: string thickness
        
        
        Returns: error code
        """
    def get_url(self) -> str:
        """
        Get url of rtsp
        
        Returns: url of rtsp
        """
    def get_urls(self) -> list[str]:
        """
        Get url list of rtsp
        
        Returns: url list of rtsp
        """
    def start(self) -> maix._maix.err.Err:
        """
        start rtsp
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def stop(self) -> maix._maix.err.Err:
        """
        stop rtsp
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def to_camera(self) -> maix._maix.camera.Camera:
        """
        Get camera object from rtsp
        
        Returns: camera object
        """
    def update_region(self, region: Region) -> maix._maix.err.Err:
        """
        update and show region(This function will be removed in the future)
        
        Returns: error code
        """
    def write(self, frame: maix._maix.video.Frame) -> maix._maix.err.Err:
        """
        Write data to rtsp(This function will be removed in the future)
        
        Args:
          - frame: video frame data
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
class RtspStreamType:
    """
    Members:
    
      RTSP_STREAM_NONE
    
      RTSP_STREAM_H264
    
      RTSP_STREAM_H265
    """
    RTSP_STREAM_H264: typing.ClassVar[RtspStreamType]  # value = <RtspStreamType.RTSP_STREAM_H264: 1>
    RTSP_STREAM_H265: typing.ClassVar[RtspStreamType]  # value = <RtspStreamType.RTSP_STREAM_H265: 2>
    RTSP_STREAM_NONE: typing.ClassVar[RtspStreamType]  # value = <RtspStreamType.RTSP_STREAM_NONE: 0>
    __members__: typing.ClassVar[dict[str, RtspStreamType]]  # value = {'RTSP_STREAM_NONE': <RtspStreamType.RTSP_STREAM_NONE: 0>, 'RTSP_STREAM_H264': <RtspStreamType.RTSP_STREAM_H264: 1>, 'RTSP_STREAM_H265': <RtspStreamType.RTSP_STREAM_H265: 2>}
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
