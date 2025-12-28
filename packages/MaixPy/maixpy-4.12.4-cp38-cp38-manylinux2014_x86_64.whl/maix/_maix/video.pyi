"""
maix.video module
"""
from __future__ import annotations
import maix._maix.audio
import maix._maix.camera
import maix._maix.display
import maix._maix.err
import maix._maix.image
import typing
__all__: list[str] = ['Context', 'Decoder', 'Encoder', 'Frame', 'MediaType', 'Packet', 'Video', 'VideoRecorder', 'VideoType', 'timebase_to_ms', 'timebase_to_us']
class Context:
    @staticmethod
    def get_pcm(*args, **kwargs):
        """
        Get pcm data (only valid in the context of audio)
        
        Returns: Bytes
        """
    def __init__(self, media_type: MediaType, timebase: list[int]) -> None:
        ...
    def audio_channels(self) -> int:
        """
        Get channels of audio (only valid in the context of audio)
        
        Returns: channels
        """
    def audio_format(self) -> maix._maix.audio.Format:
        """
        Get format of audio (only valid in the context of audio)
        
        Returns: audio format. @see audio::Format
        """
    def audio_sample_rate(self) -> int:
        """
        Get sample rate of audio (only valid in the context of audio)
        
        Returns: sample rate
        """
    def duration(self) -> int:
        """
        Duration of the current frame. unit: timebase
        """
    def duration_us(self) -> int:
        """
        Duration of the current frame. unit: us
        """
    def image(self) -> maix._maix.image.Image:
        """
        Retrieve the image data to be played.
        """
    def last_pts(self) -> int:
        """
        Get the start time of the previous playback, in units of time base.
        """
    def media_type(self) -> MediaType:
        """
        Get the media type to determine whether it is video, audio, or another media type.
        """
    def pts(self) -> int:
        """
        Get the start time of the current playback., in units of time base.
        """
    def set_pcm(self, data: maix.Bytes(bytes), duration: int = 0, pts: int = 0, copy: bool = True) -> maix._maix.err.Err:
        """
        Set pcm data (only valid in the context of audio)
        
        Args:
          - duration: Duration of the current pcm. unit: timebase
          - pts: The start time of this pcm playback. If it is 0, it means this parameter is not supported. unit: timebase
        
        
        Returns: err::Err
        """
    def timebase(self) -> list[int]:
        """
        Get the time base.
        """
class Decoder:
    def __init__(self, path: str, format: maix._maix.image.Format = ...) -> None:
        ...
    def audio_channels(self) -> int:
        """
        Get channels of audio (only valid in the context of audio)
        
        Returns: channels
        """
    def audio_format(self) -> maix._maix.audio.Format:
        """
        Get format of audio (only valid in the context of audio)
        
        Returns: audio format. @see audio::Format
        """
    def audio_sample_rate(self) -> int:
        """
        Get sample rate of audio (only valid in the context of audio)
        
        Returns: sample rate
        """
    def bitrate(self) -> int:
        """
        Get the video bitrate
        
        Returns: bitrate value
        """
    def decode(self, block: bool = True) -> Context:
        """
        Decode the video and audio stream
        
        Args:
          - block: Whether it blocks or not. If true, it will wait for the decoding to complete and return the current frame.
        If false, it will return the result of the previous frame's decoding. If the previous frame's decoding result is empty,
        it will return an unknown Context, and you can use the media_type method of the Context to determine if a valid result exists.
        default is true.
        
        
        Returns: Decoded context information.
        """
    def decode_audio(self) -> Context:
        """
        Decode the video stream, returning the image of the next frame each time.
        
        Returns: Decoded context information.
        """
    def decode_video(self, block: bool = True) -> Context:
        """
        Decode the video stream, returning the image of the next frame each time.
        
        Args:
          - block: Whether it blocks or not. If true, it will wait for the decoding to complete and return the current frame.
        If false, it will return the result of the previous frame's decoding. If the previous frame's decoding result is empty,
        it will return an unknown Context, and you can use the media_type method of the Context to determine if a valid result exists.
        default is true.
        
        
        Returns: Decoded context information.
        """
    def duration(self) -> float:
        """
        Get the maximum duration of the video. If it returns 0, it means it cannot be predicted.
        
        Returns: duration value, unit: s
        """
    def fps(self) -> int:
        """
        Get the video fps
        
        Returns: fps value
        """
    def has_audio(self) -> bool:
        """
        If find audio data, return true
        """
    def has_video(self) -> bool:
        """
        If find video data, return true
        """
    def height(self) -> int:
        """
        Get the video height
        
        Returns: video height
        """
    def pop(self, block_ms: int = 1000) -> ...:
        """
        Pop a frame from encoder.
        
        Args:
          - block_ms: block read, if block_ms = -1, block indefinitely until an image is read; if block_ms = 0, do not block and return immediately
        
        
        Returns: pop result. @see pipeline::Frame
        """
    def push(self, stream: ...) -> maix._maix.err.Err:
        """
        Push a pipeline frame to encoder.
        
        Args:
          - stream: the frame will be push.
        
        
        Returns: push result
        """
    def seek(self, time: float = -1) -> float:
        """
        Seek to the required playback position
        
        Args:
          - time: timestamp value, unit: s
        
        
        Returns: return the current position, unit: s
        """
    def timebase(self) -> list[int]:
        """
        Get the time base.
        """
    def width(self) -> int:
        """
        Get the video width
        
        Returns: video width
        """
class Encoder:
    def __init__(self, path: str = '', width: int = 2560, height: int = 1440, format: maix._maix.image.Format = ..., type: VideoType = ..., framerate: int = 30, gop: int = 50, bitrate: int = 3000000, time_base: int = 1000, capture: bool = False, block: bool = True) -> None:
        ...
    def bind_camera(self, camera: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind camera
        
        Args:
          - camera: camera object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def bitrate(self) -> int:
        """
        Get video encode bitrate
        
        Returns: bitrate value
        """
    def capture(self) -> maix._maix.image.Image:
        """
        Capture image
        
        Returns: error code
        """
    def encode(self, img: maix._maix.image.Image = ..., pcm: maix.Bytes(bytes) = b'') -> Frame:
        """
        Encode image.
        
        Args:
          - img: the image will be encode.
        if the img is NULL, this function will try to get image from camera, you must use bind_camera() function to bind the camera.
          - pcm: the pcm data will be encode.
        
        
        Returns: encode result
        """
    def format(self) -> maix._maix.image.Format:
        """
        Get video format
        
        Returns: video format
        """
    def framerate(self) -> int:
        """
        Get video encode framerate
        
        Returns: frame rate
        """
    def gop(self) -> int:
        """
        Get video encode gop
        
        Returns: gop value
        """
    def height(self) -> int:
        """
        Get video height
        
        Returns: video height
        """
    def pop(self, block_ms: int = 1000) -> ...:
        """
        Pop a frame from encoder.
        
        Args:
          - block_ms: block read, if block_ms = -1, block indefinitely until an image is read; if block_ms = 0, do not block and return immediately
        
        
        Returns: pop result. @see pipeline::Stream
        """
    def push(self, frame: ...) -> maix._maix.err.Err:
        """
        Push a pipeline frame to encoder.
        
        Args:
          - frame: the frame will be push.
        
        
        Returns: push result
        """
    def time_base(self) -> int:
        """
        Get video encode time base
        
        Returns: time base value
        """
    def type(self) -> VideoType:
        """
        Get video encode type
        
        Returns: VideoType
        """
    def width(self) -> int:
        """
        Get video width
        
        Returns: video width
        """
class Frame:
    @staticmethod
    def to_bytes(*args, **kwargs):
        """
        Get raw data of packet
        
        Args:
          - copy: if true, will alloc memory and copy data to new buffer
        
        
        Returns: raw data
        """
    def get_dts(self) -> int:
        """
        Set dts
        
        Args:
          - dts: decoding time stamp.  unit: time_base
        
        
        Returns: dts value
        """
    def get_duration(self) -> int:
        """
        Get duration
        
        Returns: duration value
        """
    def get_pts(self) -> int:
        """
        Set pts
        
        Args:
          - pts: presentation time stamp. unit: time_base
        
        
        Returns: pts value
        """
    def is_valid(self) -> bool:
        """
        Check packet is valid
        
        Returns: true, packet is valid; false, packet is invalid
        """
    def set_dts(self, dts: int) -> None:
        """
        Set dts
        
        Args:
          - dts: decoding time stamp.  unit: time_base
        """
    def set_duration(self, duration: int) -> None:
        """
        Set duration
        
        Args:
          - duration: packet display time. unit: time_base
        """
    def set_pts(self, pts: int) -> None:
        """
        Set pts
        
        Args:
          - pts: presentation time stamp. unit: time_base
        """
    def size(self) -> int:
        """
        Get raw data size of packet
        
        Returns: size of raw data
        """
    def type(self) -> VideoType:
        """
        Get frame type
        
        Returns: video type. @see video::VideoType
        """
class MediaType:
    """
    Members:
    
      MEDIA_TYPE_UNKNOWN
    
      MEDIA_TYPE_VIDEO
    
      MEDIA_TYPE_AUDIO
    
      MEDIA_TYPE_DATA
    
      MEDIA_TYPE_SUBTITLE
    
      MEDIA_TYPE_ATTACHMENT
    
      MEDIA_TYPE_NB
    """
    MEDIA_TYPE_ATTACHMENT: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_ATTACHMENT: 4>
    MEDIA_TYPE_AUDIO: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_AUDIO: 1>
    MEDIA_TYPE_DATA: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_DATA: 2>
    MEDIA_TYPE_NB: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_NB: 5>
    MEDIA_TYPE_SUBTITLE: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_SUBTITLE: 3>
    MEDIA_TYPE_UNKNOWN: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_UNKNOWN: -1>
    MEDIA_TYPE_VIDEO: typing.ClassVar[MediaType]  # value = <MediaType.MEDIA_TYPE_VIDEO: 0>
    __members__: typing.ClassVar[dict[str, MediaType]]  # value = {'MEDIA_TYPE_UNKNOWN': <MediaType.MEDIA_TYPE_UNKNOWN: -1>, 'MEDIA_TYPE_VIDEO': <MediaType.MEDIA_TYPE_VIDEO: 0>, 'MEDIA_TYPE_AUDIO': <MediaType.MEDIA_TYPE_AUDIO: 1>, 'MEDIA_TYPE_DATA': <MediaType.MEDIA_TYPE_DATA: 2>, 'MEDIA_TYPE_SUBTITLE': <MediaType.MEDIA_TYPE_SUBTITLE: 3>, 'MEDIA_TYPE_ATTACHMENT': <MediaType.MEDIA_TYPE_ATTACHMENT: 4>, 'MEDIA_TYPE_NB': <MediaType.MEDIA_TYPE_NB: 5>}
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
class Packet:
    def __init__(self, data: int, len: int, pts: int = -1, dts: int = -1, duration: int = 0) -> None:
        ...
    def data(self) -> int:
        """
        Get raw data of packet
        
        Returns: raw data
        """
    def data_size(self) -> int:
        """
        Get raw data size of packet
        
        Returns: size of raw data
        """
    def get(self) -> list[int]:
        """
        Get raw data of packet
        
        Returns: raw data
        """
    def is_valid(self) -> bool:
        """
        Check packet is valid
        
        Returns: true, packet is valid; false, packet is invalid
        """
    def set_dts(self, dts: int) -> None:
        """
        Set dts
        
        Args:
          - dts: decoding time stamp.  unit: time_base
        
        
        Returns: true, packet is valid; false, packet is invalid
        """
    def set_duration(self, duration: int) -> None:
        """
        Set duration
        
        Args:
          - duration: packet display time. unit: time_base
        
        
        Returns: true, packet is valid; false, packet is invalid
        """
    def set_pts(self, pts: int) -> None:
        """
        Set pts
        
        Args:
          - pts: presentation time stamp. unit: time_base
        
        
        Returns: true, packet is valid; false, packet is invalid
        """
class Video:
    def __init__(self, path: str = '', width: int = 2560, height: int = 1440, format: maix._maix.image.Format = ..., time_base: int = 30, framerate: int = 30, capture: bool = False, open: bool = True) -> None:
        ...
    def bind_camera(self, camera: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind camera
        
        Args:
          - camera: camera object
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def capture(self) -> maix._maix.image.Image:
        """
        Capture image
        
        Returns: error code
        """
    def close(self) -> None:
        """
        Close video
        """
    def decode(self, frame: Frame = None) -> maix._maix.image.Image:
        """
        Decode frame
        
        Args:
          - frame: the frame will be decode
        
        
        Returns: decode result
        """
    def encode(self, img: maix._maix.image.Image = ...) -> Packet:
        """
        Encode image.
        
        Args:
          - img: the image will be encode.
        if the img is NULL, this function will try to get image from camera, you must use bind_camera() function to bind the camera.
        
        
        Returns: encode result
        """
    def finish(self) -> maix._maix.err.Err:
        """
        Encode or decode finish
        
        Returns: error code
        """
    def height(self) -> int:
        """
        Get video height
        
        Returns: video height
        """
    def is_closed(self) -> bool:
        """
        check video device is closed or not
        
        Returns: closed or not, bool type
        """
    def is_opened(self) -> bool:
        """
        Check if video is opened
        
        Returns: true if video is opened, false if not
        """
    def is_recording(self) -> bool:
        """
        Check if video is recording
        
        Returns: true if video is recording, false if not
        """
    def open(self, path: str = '', fps: float = 30.0) -> maix._maix.err.Err:
        """
        Open video and run
        
        Args:
          - path: video path. the path determines the location where you load or save the file, if path is none, the video module will not save or load file.
        xxx.h265 means video format is H265, xxx.mp4 means video format is MP4
          - fps: video fps
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def width(self) -> int:
        """
        Get video width
        
        Returns: video width
        """
class VideoRecorder:
    def __init__(self, open: bool = True) -> None:
        ...
    def bind_audio(self, audio: maix._maix.audio.Recorder) -> maix._maix.err.Err:
        """
        Bind a AudioRecorder object. if this object is not bound, audio cannot be captured.
        
        Args:
          - audio: audio recorder object
        
        
        Returns: error code
        """
    def bind_camera(self, camera: maix._maix.camera.Camera) -> maix._maix.err.Err:
        """
        Bind a Camera object. if this object is not bound, images cannot be captured.
        
        Args:
          - camera: camera object
        
        
        Returns: error code
        """
    def bind_display(self, display: maix._maix.display.Display, fit: maix._maix.image.Fit = ...) -> maix._maix.err.Err:
        """
        Bind a Display object. if this object is not bound, it will not be displayed.
        
        Args:
          - display: display object
          - fit: fit mode. It is recommended to fill in FIT_COVER or FIT_FILL. For maixcam, using FIT_CONTAIN may affect the
        functionality of the second layer created by add_channel() in the Display. default is FIT_COVER.
        
        
        Returns: error code
        """
    def bind_imu(self, imu: capsule) -> maix._maix.err.Err:
        """
        Bind a IMU object. if this object is not bound, imu data cannot be captured.
        
        Args:
          - imu: imu object
        
        
        Returns: error code
        """
    def close(self) -> maix._maix.err.Err:
        """
        Stop the thread, and reset the object.
        
        Returns: error code
        """
    def config_bitrate(self, bitrate: int) -> maix._maix.err.Err:
        """
        Set the bitrate of the video, and this API cannot be called during runtime.
        
        Returns: error code
        """
    def config_fps(self, fps: int) -> maix._maix.err.Err:
        """
        Set the fps of the video, and this API cannot be called during runtime.
        
        Returns: error code
        """
    def config_path(self, path: str) -> maix._maix.err.Err:
        """
        The recorded video will be saved to this path, and this API cannot be called during runtime.
        
        Args:
          - path: The path of the video file to be saved
        
        
        Returns: error code
        """
    def config_resolution(self, resolution: list[int]) -> maix._maix.err.Err:
        """
        Set the resolution of the video, and this API cannot be called during runtime.
        
        Args:
          - resolution: The resolution of the video
        
        
        Returns: error code
        """
    def config_snapshot(self, enable: bool, resolution: list[int] = [], format: maix._maix.image.Format = ...) -> maix._maix.err.Err:
        """
        Set the snapshot parameters
        
        Args:
          - enable: enable or disable snapshot
          - resolution: image resolution of snapshot
          - format: image format of snapshot
        
        
        Returns: error code
        """
    def draw_rect(self, id: int, x: int, y: int, w: int, h: int, color: maix._maix.image.Color = ..., thickness: int = -1, hidden: bool = False) -> maix._maix.err.Err:
        """
        Draw a rect on the video
        
        Args:
          - id: id of the rect, range is [0, 15]
          - x: x coordinate
          - y: y coordinate
          - w: width
          - h: height
          - color: color
          - tickness: The line width of the rectangular box; if set to -1, it indicates that the rectangular box will be filled.
          - hidden: Hide or show the rectangular box
        
        
        Returns: error code
        """
    def get_bitrate(self) -> int:
        """
        Get the bitrate of the video.
        
        Returns: bitrate value
        """
    def get_fps(self) -> int:
        """
        Get the fps of the video.
        
        Returns: fps value
        """
    def get_path(self) -> str:
        """
        Get the path of the video file to be saved
        
        Returns: path
        """
    def get_resolution(self) -> list[int]:
        """
        Get the resolution of the video
        
        Returns: the resolution of the video
        """
    def is_opened(self) -> bool:
        """
        Check whether the object is opened.
        """
    def lock(self, timeout: int = -1) -> maix._maix.err.Err:
        """
        lock video
        
        Args:
          - timeout: timeout in ms. unit:ms
        
        
        Returns: error code
        """
    def mute(self, data: int = -1) -> int:
        """
        Set/Get the mute of the video
        
        Args:
          - data: If the parameter is true, mute; if false, unmute; if no parameter is provided, return the mute status.
        
        
        Returns: error code
        """
    def open(self) -> maix._maix.err.Err:
        """
        Start a thread to handle the input function.
        
        Returns: error code
        """
    def record_finish(self) -> maix._maix.err.Err:
        """
        Stop recording and save the video
        
        Returns: error code
        """
    def record_start(self) -> maix._maix.err.Err:
        """
        Start recording
        
        Returns: error code
        """
    def reset(self) -> maix._maix.err.Err:
        """
        Reset the video recorder.
        
        Returns: error code
        """
    def seek(self) -> int:
        """
        Get the current position of the video
        
        Returns: current position, unit: ms
        """
    def snapshot(self) -> maix._maix.image.Image:
        """
        Take a snapshot
        
        Returns: image::Image
        """
    def unlock(self) -> maix._maix.err.Err:
        """
        unlock video
        
        Returns: error code
        """
    def volume(self, data: int = -1) -> int:
        """
        Set/Get the volume of the video
        
        Args:
          - data: The volume of the video, the range is 0-100. if no parameter is provided, return the volume.
        
        
        Returns: error code
        """
class VideoType:
    """
    Members:
    
      VIDEO_NONE
    
      VIDEO_ENC_H265_CBR
    
      VIDEO_ENC_MP4_CBR
    
      VIDEO_DEC_H265_CBR
    
      VIDEO_DEC_MP4_CBR
    
      VIDEO_H264_CBR
    
      VIDEO_H265_CBR
    
      VIDEO_H264_CBR_MP4
    
      VIDEO_H265_CBR_MP4
    
      VIDEO_H264
    
      VIDEO_H264_MP4
    
      VIDEO_H264_FLV
    
      VIDEO_H265
    
      VIDEO_H265_MP4
    """
    VIDEO_DEC_H265_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_DEC_H265_CBR: 3>
    VIDEO_DEC_MP4_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_DEC_MP4_CBR: 4>
    VIDEO_ENC_H265_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_ENC_H265_CBR: 1>
    VIDEO_ENC_MP4_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_ENC_MP4_CBR: 2>
    VIDEO_H264: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H264: 9>
    VIDEO_H264_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H264_CBR: 5>
    VIDEO_H264_CBR_MP4: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H264_CBR_MP4: 7>
    VIDEO_H264_FLV: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H264_FLV: 11>
    VIDEO_H264_MP4: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H264_MP4: 10>
    VIDEO_H265: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H265: 12>
    VIDEO_H265_CBR: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H265_CBR: 6>
    VIDEO_H265_CBR_MP4: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H265_CBR_MP4: 8>
    VIDEO_H265_MP4: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_H265_MP4: 13>
    VIDEO_NONE: typing.ClassVar[VideoType]  # value = <VideoType.VIDEO_NONE: 0>
    __members__: typing.ClassVar[dict[str, VideoType]]  # value = {'VIDEO_NONE': <VideoType.VIDEO_NONE: 0>, 'VIDEO_ENC_H265_CBR': <VideoType.VIDEO_ENC_H265_CBR: 1>, 'VIDEO_ENC_MP4_CBR': <VideoType.VIDEO_ENC_MP4_CBR: 2>, 'VIDEO_DEC_H265_CBR': <VideoType.VIDEO_DEC_H265_CBR: 3>, 'VIDEO_DEC_MP4_CBR': <VideoType.VIDEO_DEC_MP4_CBR: 4>, 'VIDEO_H264_CBR': <VideoType.VIDEO_H264_CBR: 5>, 'VIDEO_H265_CBR': <VideoType.VIDEO_H265_CBR: 6>, 'VIDEO_H264_CBR_MP4': <VideoType.VIDEO_H264_CBR_MP4: 7>, 'VIDEO_H265_CBR_MP4': <VideoType.VIDEO_H265_CBR_MP4: 8>, 'VIDEO_H264': <VideoType.VIDEO_H264: 9>, 'VIDEO_H264_MP4': <VideoType.VIDEO_H264_MP4: 10>, 'VIDEO_H264_FLV': <VideoType.VIDEO_H264_FLV: 11>, 'VIDEO_H265': <VideoType.VIDEO_H265: 12>, 'VIDEO_H265_MP4': <VideoType.VIDEO_H265_MP4: 13>}
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
def timebase_to_ms(timebase: list[int], value: int) -> float:
    """
    Convert a value in timebase units to milliseconds.
    
    Args:
      - timebse: Time base, used as the unit for calculating playback time. It must be an array containing two parameters,
    in the format [num, den], where the first parameter is the numerator of the time base, and the second parameter is the denominator of the time base.
      - value: Input value
    
    
    Returns: Return the result in milliseconds.
    """
def timebase_to_us(timebase: list[int], value: int) -> float:
    """
    Convert a value in timebase units to microseconds. value * 1000000 / (timebase[1] / timebase[0])
    
    Args:
      - timebse: Time base, used as the unit for calculating playback time. It must be an array containing two parameters,
    in the format [num, den], where the first parameter is the numerator of the time base, and the second parameter is the denominator of the time base.
      - value: Input value
    
    
    Returns: Return the result in microseconds.
    """
