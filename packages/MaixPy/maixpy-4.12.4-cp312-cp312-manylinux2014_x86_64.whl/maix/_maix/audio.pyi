"""
maix.audio module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['File', 'Format', 'Player', 'Recorder', 'fmt_bits']
class File:
    @staticmethod
    def get_pcm(*args, **kwargs):
        """
        Get pcm data
        
        Returns: pcm data. datatype @see Bytes
        """
    def __init__(self, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> None:
        ...
    def channels(self, new_channels: int = -1) -> int:
        """
        Get channels
        
        Args:
          - new_channels: if new_channels > 0, change channels
        
        
        Returns: current channels
        """
    def load(self, path: str, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> maix._maix.err.Err:
        """
        Loads an audio file from a given file path.
        
        Args:
          - path: The file path to load the audio file from.
          - sample_rate: The sample rate of the audio file. Only required for PCM files
          - channels: The number of channels in the audio file. Only required for PCM files
          - bits_per_sample: The number of bits per sample in the audio file. Only required for PCM files
        
        
        Returns: An error code indicating whether the operation was successful or not.
        """
    def sample_bits(self, new_sample_bits: int = -1) -> int:
        """
        Get sample bit
        
        Args:
          - new_sample_bit: if new_sample_bit > 0, set sample bit
        
        
        Returns: current sample bit
        """
    def sample_rate(self, new_sample_rate: int = -1) -> int:
        """
        Get sample rate
        
        Args:
          - new_sample_rate: if new_sample_rate > 0, change sample rate
        
        
        Returns: current sample rate
        """
    def save(self, path: str) -> maix._maix.err.Err:
        """
        Saves an audio file to a given file path.
        
        Args:
          - path: The path to the file where the audio file will be saved.
        
        
        Returns: An error code indicating whether the operation was successful or not.
        """
    def set_pcm(self, new_pcm: maix.Bytes(bytes), copy: bool = True) -> None:
        """
        Set pcm data
        
        Args:
          - new_pcm: pcm data. datatype @see Bytes
        """
class Format:
    """
    Members:
    
      FMT_NONE
    
      FMT_S8
    
      FMT_S16_LE
    
      FMT_S32_LE
    
      FMT_S16_BE
    
      FMT_S32_BE
    
      FMT_U8
    
      FMT_U16_LE
    
      FMT_U32_LE
    
      FMT_U16_BE
    
      FMT_U32_BE
    """
    FMT_NONE: typing.ClassVar[Format]  # value = <Format.FMT_NONE: 0>
    FMT_S16_BE: typing.ClassVar[Format]  # value = <Format.FMT_S16_BE: 4>
    FMT_S16_LE: typing.ClassVar[Format]  # value = <Format.FMT_S16_LE: 2>
    FMT_S32_BE: typing.ClassVar[Format]  # value = <Format.FMT_S32_BE: 5>
    FMT_S32_LE: typing.ClassVar[Format]  # value = <Format.FMT_S32_LE: 3>
    FMT_S8: typing.ClassVar[Format]  # value = <Format.FMT_S8: 1>
    FMT_U16_BE: typing.ClassVar[Format]  # value = <Format.FMT_U16_BE: 9>
    FMT_U16_LE: typing.ClassVar[Format]  # value = <Format.FMT_U16_LE: 7>
    FMT_U32_BE: typing.ClassVar[Format]  # value = <Format.FMT_U32_BE: 10>
    FMT_U32_LE: typing.ClassVar[Format]  # value = <Format.FMT_U32_LE: 8>
    FMT_U8: typing.ClassVar[Format]  # value = <Format.FMT_U8: 6>
    __members__: typing.ClassVar[dict[str, Format]]  # value = {'FMT_NONE': <Format.FMT_NONE: 0>, 'FMT_S8': <Format.FMT_S8: 1>, 'FMT_S16_LE': <Format.FMT_S16_LE: 2>, 'FMT_S32_LE': <Format.FMT_S32_LE: 3>, 'FMT_S16_BE': <Format.FMT_S16_BE: 4>, 'FMT_S32_BE': <Format.FMT_S32_BE: 5>, 'FMT_U8': <Format.FMT_U8: 6>, 'FMT_U16_LE': <Format.FMT_U16_LE: 7>, 'FMT_U32_LE': <Format.FMT_U32_LE: 8>, 'FMT_U16_BE': <Format.FMT_U16_BE: 9>, 'FMT_U32_BE': <Format.FMT_U32_BE: 10>}
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
class Player:
    def __init__(self, path: str = '', sample_rate: int = 48000, format: Format = ..., channel: int = 1, block: bool = True) -> None:
        ...
    def channel(self) -> int:
        """
        Get sample channel
        
        Returns: returns sample channel
        """
    def format(self) -> Format:
        """
        Get sample format
        
        Returns: returns sample format
        """
    def frame_size(self, frame_count: int = 1) -> int:
        """
        Returns the number of bytes for frame_count frames.
        
        Args:
          - frame_count: frame count
        
        
        Returns: frame bytes
        """
    def get_remaining_frames(self) -> int:
        """
        Return the number of idle frames available for writing during playback, unit: frame. if there are no idle frames, it will cause blocking.
        
        Returns: remaining frames
        """
    def period_count(self, period_count: int = -1) -> int:
        """
        Set/Get the audio buffer count, unit: frame.
        
        Args:
          - period_count: When period_count is less than 0, the current value of period_count will be returned;
        when period_count is greater than 0, period_count will be updated, and the size of period_count after setting will be returned.
        
        
        Returns: the current period count
        """
    def period_size(self, period_size: int = -1) -> int:
        """
        Set/Get the audio buffer size, unit: frame.
        
        Args:
          - period_size: When period_size is less than 0, the current value of period_size will be returned;
        when period_size is greater than 0, period_size will be updated, and the size of period_size after setting will be returned.
        
        
        Returns: the current period size
        """
    def play(self, data: maix.Bytes(bytes) = b'') -> maix._maix.err.Err:
        """
        Play
        
        Args:
          - data: audio data, must be raw data
        
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def reset(self, start: bool = False) -> None:
        """
        Reset player status
        
        Args:
          - start: start play audio data, default is False
        """
    def sample_rate(self) -> int:
        """
        Get sample rate
        
        Returns: returns sample rate
        """
    def volume(self, value: int = -1) -> int:
        """
        Set/Get player volume
        
        Args:
          - value: volume value, If you use this parameter, audio will set the value to volume,
        if you don't, it will return the current volume. range is [0, 100].
        
        
        Returns: the current volume
        """
class Recorder:
    @staticmethod
    def record(*args, **kwargs):
        """
        Record, Read all cached data in buffer and return. If there is no audio data in the buffer, may return empty data.
        
        Args:
          - record_ms: Block and record audio data lasting `record_ms` milliseconds and save it to a file.
        
        
        Returns: pcm data. datatype @see Bytes. For MaixCDK users, you need to manually release the returned PCM object.
        """
    def __init__(self, path: str = '', sample_rate: int = 48000, format: Format = ..., channel: int = 1, block: bool = True) -> None:
        ...
    def channel(self) -> int:
        """
        Get sample channel
        
        Returns: returns sample channel
        """
    def finish(self) -> maix._maix.err.Err:
        """
        Finish the record, if you have passed in the path, this api will save the audio data to file.
        
        Returns: error code, err::ERR_NONE means success, others means failed
        """
    def format(self) -> Format:
        """
        Get sample format
        
        Returns: returns sample format
        """
    def frame_size(self, frame_count: int = 1) -> int:
        """
        Returns the number of bytes for frame_count frames.
        
        Args:
          - frame_count: frame count
        
        
        Returns: frame bytes
        """
    def get_remaining_frames(self) -> int:
        """
        Return the number of frames available for reading during recording, unit is frame.
        
        Returns: remaining frames
        """
    def mute(self, data: int = -1) -> bool:
        """
        Mute
        
        Args:
          - data: mute data, If you set this parameter to true, audio will set the value to mute,
        if you don't, it will return the current mute status.
        
        
        Returns: Returns whether mute is currently enabled.
        """
    def period_count(self, period_count: int = -1) -> int:
        """
        Set/Get the audio buffer count, unit: frame.
        
        Args:
          - period_count: When period_count is less than 0, the current value of period_count will be returned;
        when period_count is greater than 0, period_count will be updated, and the size of period_count after setting will be returned.
        
        
        Returns: the current period size
        """
    def period_size(self, period_size: int = -1) -> int:
        """
        Set/Get the audio buffer size, unit: frame.
        
        Args:
          - period_size: When period_size is less than 0, the current value of period_size will be returned;
        when period_size is greater than 0, period_size will be updated, and the size of period_size after setting will be returned.
        
        
        Returns: the current period size
        """
    def reset(self, start: bool = True) -> None:
        """
        Reset record status
        
        Args:
          - start: start prepare audio data, default is True
        """
    def sample_rate(self) -> int:
        """
        Get sample rate
        
        Returns: returns sample rate
        """
    def volume(self, value: int = -1) -> int:
        """
        Set/Get record volume
        
        Args:
          - value: volume value, If you use this parameter, audio will set the value to volume,
        if you don't, it will return the current volume. range is [0, 100].
        
        
        Returns: the current volume
        """
fmt_bits: list = [0, 8, 16, 32, 16, 32, 8, 16, 32, 16, 32]
