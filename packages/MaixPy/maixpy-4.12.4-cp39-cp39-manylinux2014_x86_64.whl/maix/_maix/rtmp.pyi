"""
maix.rtmp module
"""
from __future__ import annotations
import maix._maix.audio
import maix._maix.camera
import maix._maix.display
import maix._maix.err
import typing
__all__: list[str] = ['Rtmp', 'TagType']
class Rtmp:
    def __init__(self, host: str = 'localhost', port: int = 1935, app: str = '', stream: str = '', bitrate: int = 1000000) -> None:
        ...
    def bind_audio_recorder(self, recorder: maix._maix.audio.Recorder) -> maix._maix.err.Err:
        """
        Bind audio recorder
        
        Args:
          - recorder: audio_recorder object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def bind_camera(self, cam: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind camera
        
        Args:
          - cam: camera object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def bind_display(self, display: maix._maix.display.Display) -> maix._maix.err.Err:
        """
        Bind display
        
        Args:
          - disaply: display object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def bitrate(self) -> int:
        """
        Get bitrate
        
        Returns: bitrate
        """
    def get_camera(self) -> maix._maix.camera.Camera:
        """
        If you bind a camera, return the camera object.
        
        Returns: Camera object
        """
    def get_path(self) -> str:
        """
        Get the file path of the push stream
        
        Returns: file path
        """
    def is_started(self) -> bool:
        """
        Check whether push streaming has started
        
        Returns: If rtmp thread is running, returns true
        """
    def start(self, path: str = '') -> maix._maix.err.Err:
        """
        Start push stream
        
        Args:
          - path: File path, if you passed file path, cyclic push the file, else if you bound camera, push the camera image.(This parameter has been deprecated)
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def stop(self) -> maix._maix.err.Err:
        """
        Stop push stream
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
class TagType:
    """
    Members:
    
      TAG_NONE
    
      TAG_VIDEO
    
      TAG_AUDIO
    
      TAG_SCRIPT
    """
    TAG_AUDIO: typing.ClassVar[TagType]  # value = <TagType.TAG_AUDIO: 2>
    TAG_NONE: typing.ClassVar[TagType]  # value = <TagType.TAG_NONE: 0>
    TAG_SCRIPT: typing.ClassVar[TagType]  # value = <TagType.TAG_SCRIPT: 3>
    TAG_VIDEO: typing.ClassVar[TagType]  # value = <TagType.TAG_VIDEO: 1>
    __members__: typing.ClassVar[dict[str, TagType]]  # value = {'TAG_NONE': <TagType.TAG_NONE: 0>, 'TAG_VIDEO': <TagType.TAG_VIDEO: 1>, 'TAG_AUDIO': <TagType.TAG_AUDIO: 2>, 'TAG_SCRIPT': <TagType.TAG_SCRIPT: 3>}
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
