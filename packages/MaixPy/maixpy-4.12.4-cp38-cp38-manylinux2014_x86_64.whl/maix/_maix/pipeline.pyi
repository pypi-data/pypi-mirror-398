"""
maix.pipeline module, video stream processing via pipeline
"""
from __future__ import annotations
import maix._maix.image
__all__: list[str] = ['Frame', 'Stream']
class Frame:
    def __init__(self, frame: capsule, auto_delete: bool = False, from: str = '') -> None:
        ...
    def format(self) -> maix._maix.image.Format:
        """
        Get the format of the frame
        
        Returns: Returns the format of the frame.
        """
    def height(self) -> int:
        """
        Get the height of the frame
        
        Returns: Returns the height of the frame.
        """
    def physical_address(self, idx: int) -> int:
        """
        Get the physical address of the plane. In image processing, different image formats are divided into multiple planes.
        Typically, RGB images have only one valid plane, while NV21/NV12 images have two valid planes.
        
        Args:
          - idx: plane index.
        
        
        Returns: Returns the physical address of the frame.
        """
    def stride(self, idx: int) -> int:
        """
        Get the stride of the plane. Stride represents the number of bytes occupied in memory by each row of image data.
        It is usually greater than or equal to the number of bytes actually used by the pixels in that row.
        In image processing, different image formats are divided into multiple planes.
        Typically, RGB images have only one valid plane, while NV21/NV12 images have two valid planes.
        
        Args:
          - idx: plane index.
        
        
        Returns: Returns the stride of the frame.
        """
    def to_image(self) -> maix._maix.image.Image:
        """
        Convert the frame to an image
        
        Returns: Returns an image object.
        """
    def virtual_address(self, idx: int) -> int:
        """
        Get the virtual address of the plane. In image processing, different image formats are divided into multiple planes.
        Typically, RGB images have only one valid plane, while NV21/NV12 images have two valid planes.
        
        Args:
          - idx: plane index.
        
        
        Returns: Returns the virtual address of the frame.
        """
    def width(self) -> int:
        """
        Get the width of the frame
        
        Returns: Returns the width of the frame.
        """
class Stream:
    @staticmethod
    def data(*args, **kwargs):
        """
        Get the data stream at index
        
        Args:
          - idx: data index, must be less than data_count().
        
        
        Returns: Returns the data at index. Note: when using C++, you need to manually release the memory.
        """
    @staticmethod
    def get_i_frame(*args, **kwargs):
        """
        Get the I frame data; if the frame does not exist, return null.
        
        Returns: I frame data.
        """
    @staticmethod
    def get_p_frame(*args, **kwargs):
        """
        Get the PTS(Presentation Timestamp) of the stream.
        
        Returns: P frame data.
        """
    @staticmethod
    def get_pps_frame(*args, **kwargs):
        """
        Get the PPS frame data; if the frame does not exist, return null.
        
        Returns: PPS frame data.
        """
    @staticmethod
    def get_sps_frame(*args, **kwargs):
        """
        Get the SPS frame data; if the frame does not exist, return null.
        
        Returns: SPS frame data.
        """
    def data_count(self) -> int:
        """
        Since a single stream may contain multiple pieces of data, this returns the number of data segments present.
        """
    def data_size(self, idx: int) -> int:
        """
        Get the data size at index
        
        Args:
          - idx: data index, must be less than data_count().
        
        
        Returns: Returns the data size at index.
        """
    def has_i_frame(self) -> bool:
        """
        Check if the stream has I frame.
        
        Returns: True if the stream has I frame, otherwise false.
        """
    def has_p_frame(self) -> bool:
        """
        Check if the stream has P frame.
        
        Returns: True if the stream has P frame, otherwise false.
        """
    def has_pps_frame(self) -> bool:
        """
        Check if the stream has PPS frame.
        
        Returns: PPS frame data.
        """
    def has_sps_frame(self) -> bool:
        """
        Check if the stream has SPS frame.
        
        Returns: SPS frame data.
        """
    def pts(self) -> int:
        """
        Get the pts(Presentation Timestamp) of the stream
        
        Returns: Returns the pts of the stream.
        """
