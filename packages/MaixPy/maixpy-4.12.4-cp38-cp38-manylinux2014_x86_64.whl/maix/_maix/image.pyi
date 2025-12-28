"""
maix.image module, image related definition and functions
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.tensor
import pybind11_stubgen.typing_ext
import typing
import typing_extensions
__all__: list[str] = ['AprilTag', 'ApriltagFamilies', 'BarCode', 'Blob', 'CMap', 'COLOR_BLACK', 'COLOR_BLUE', 'COLOR_GRAY', 'COLOR_GREEN', 'COLOR_INVALID', 'COLOR_ORANGE', 'COLOR_PURPLE', 'COLOR_RED', 'COLOR_WHITE', 'COLOR_YELLOW', 'Circle', 'Color', 'CornerDetector', 'DataMatrix', 'Displacement', 'EdgeDetector', 'Fit', 'FlipDir', 'Format', 'HaarCascade', 'Histogram', 'Image', 'KPTMatch', 'KeyPoint', 'LBPKeyPoint', 'Line', 'LineGroup', 'LineType', 'ORBKeyPoint', 'Percentile', 'QRCode', 'QRCodeDecoderType', 'QRCodeDetector', 'Rect', 'ResizeMethod', 'Size', 'Statistics', 'TemplateMatch', 'Threshold', 'cmap_color', 'cmap_colors', 'cmap_colors_rgb', 'cmap_from_str', 'cmap_strs', 'cmap_to_str', 'cv2image', 'fmt_names', 'fmt_size', 'fonts', 'format_name', 'from_bytes', 'image2cv', 'load', 'load_font', 'resize_map_pos', 'resize_map_pos_reverse', 'set_default_font', 'string_size']
class AprilTag:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] Returns the apriltag’s bounding box x coordinate
        [1] Returns the apriltag’s bounding box y coordinate
        [2] Returns the apriltag’s bounding box w coordinate
        [3] Returns the apriltag’s bounding box h coordinate
        [4] Returns the apriltag’s id
        [5] Returns the apriltag’s family
        [6] Not support
        [7] Not support
        [8] Not support
        [9] Not support
        [10] Returns the apriltag’s hamming
        [11] Not support
        [12] Not support
        [13] Not support
        [14] Not support
        [15] Not support
        [16] Not support
        [17] Not support
        
        
        Returns: int&
        """
    def __init__(self, rect: list[int], corners: list[list[int]], id: int, famliy: int, centroid_x: float, centroid_y: float, rotation: float, decision_margin: float, hamming: int, goodness: float, x_translation: float, y_translation: float, z_translation: float, x_rotation: float, y_rotation: float, z_rotation: float) -> None:
        ...
    def corners(self) -> list[list[int]]:
        """
        get coordinate of AprilTag
        
        Returns: return the coordinate of the AprilTag.
        """
    def cx(self) -> int:
        """
        get cx of AprilTag
        
        Returns: return cx of the AprilTag, type is int
        """
    def cxf(self) -> float:
        """
        get cxf of AprilTag
        
        Returns: return cxf of the AprilTag, type is float
        """
    def cy(self) -> int:
        """
        get cy of AprilTag
        
        Returns: return cy of the AprilTag, type is int
        """
    def cyf(self) -> float:
        """
        get cyf of AprilTag
        
        Returns: return cyf of the AprilTag, type is float
        """
    def decision_margin(self) -> float:
        """
        Get decision_margin of AprilTag
        
        Returns: Returns the quality of the apriltag match (0.0 - 1.0) where 1.0 is the best.
        """
    def family(self) -> int:
        """
        get family of AprilTag
        
        Returns: return family of the AprilTag, type is int
        """
    def goodness(self) -> float:
        """
        get goodness of AprilTag
        
        Returns: return goodness of the AprilTag, type is float
        Note: This value is always 0.0 for now.
        """
    def h(self) -> int:
        """
        get h of AprilTag
        
        Returns: return h of the AprilTag, type is int
        """
    def hamming(self) -> int:
        """
        get hamming of AprilTag
        
        Returns: Returns the number of accepted bit errors for this tag.
        return 0, means 0 bit errors will be accepted.
        1 is TAG25H7, means up to 1 bit error may be accepted
        2 is TAG25H9, means up to 3 bit errors may be accepted
        3 is TAG36H10, means up to 3 bit errors may be accepted
        4 is TAG36H11, means up to 4 bit errors may be accepted
        5 is ARTOOLKIT, means 0 bit errors will be accepted
        """
    def id(self) -> int:
        """
        get id of AprilTag
        
        Returns: return id of the AprilTag, type is int
        """
    def rect(self) -> list[int]:
        """
        get rectangle of AprilTag
        
        Returns: return the rectangle of the AprilTag. format is {x, y, w, h}, type is std::vector<int>
        """
    def rotation(self) -> float:
        """
        get rotation of AprilTag
        
        Returns: return rotation of the AprilTag, type is float
        """
    def w(self) -> int:
        """
        get w of AprilTag
        
        Returns: return w of the AprilTag, type is int
        """
    def x(self) -> int:
        """
        get x of AprilTag
        
        Returns: return x of the AprilTag, type is int
        """
    def x_rotation(self) -> float:
        """
        get x_rotation of AprilTag
        
        Returns: return x_rotation of the AprilTag, type is float
        """
    def x_translation(self) -> float:
        """
        get x_translation of AprilTag
        
        Returns: return x_translation of the AprilTag, type is float
        """
    def y(self) -> int:
        """
        get y of AprilTag
        
        Returns: return y of the AprilTag, type is int
        """
    def y_rotation(self) -> float:
        """
        get y_rotation of AprilTag
        
        Returns: return y_rotation of the AprilTag, type is float
        """
    def y_translation(self) -> float:
        """
        get y_translation of AprilTag
        
        Returns: return y_translation of the AprilTag, type is float
        """
    def z_rotation(self) -> float:
        """
        get z_rotation of AprilTag
        
        Returns: return z_rotation of the AprilTag, type is float
        """
    def z_translation(self) -> float:
        """
        get z_translation of AprilTag
        
        Returns: return z_translation of the AprilTag, type is float
        """
class ApriltagFamilies:
    """
    Members:
    
      TAG16H5
    
      TAG25H7
    
      TAG25H9
    
      TAG36H10
    
      TAG36H11
    
      ARTOOLKIT
    """
    ARTOOLKIT: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.ARTOOLKIT: 32>
    TAG16H5: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.TAG16H5: 1>
    TAG25H7: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.TAG25H7: 2>
    TAG25H9: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.TAG25H9: 4>
    TAG36H10: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.TAG36H10: 8>
    TAG36H11: typing.ClassVar[ApriltagFamilies]  # value = <ApriltagFamilies.TAG36H11: 16>
    __members__: typing.ClassVar[dict[str, ApriltagFamilies]]  # value = {'TAG16H5': <ApriltagFamilies.TAG16H5: 1>, 'TAG25H7': <ApriltagFamilies.TAG25H7: 2>, 'TAG25H9': <ApriltagFamilies.TAG25H9: 4>, 'TAG36H10': <ApriltagFamilies.TAG36H10: 8>, 'TAG36H11': <ApriltagFamilies.TAG36H11: 16>, 'ARTOOLKIT': <ApriltagFamilies.ARTOOLKIT: 32>}
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
class BarCode:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] get x of BarCode
        [1] get y of BarCode
        [2] get w of BarCode
        [3] get h of BarCode
        [4] Not support this index, try to use payload() method
        [5] get type of BarCode
        [6] Not support this index, try to use rotation() method
        [7] get quality of BarCode
        
        
        Returns: int&
        """
    def __init__(self, rect: list[int], corners: list[list[int]], payload: str, type: int, rotation: float, quality: int) -> None:
        ...
    def corners(self) -> list[list[int]]:
        """
        get coordinate of BarCode
        
        Returns: return the coordinate of the BarCode.
        """
    def h(self) -> int:
        """
        get h of BarCode
        
        Returns: return h of the BarCode, type is int
        """
    def payload(self) -> str:
        """
        get payload of BarCode
        
        Returns: return payload of the BarCode, type is std::string
        """
    def quality(self) -> int:
        """
        get quality of BarCode
        
        Returns: return quality of the BarCode, type is int
        """
    def rect(self) -> list[int]:
        """
        get rectangle of BarCode
        
        Returns: return the rectangle of the BarCode. format is {x, y, w, h}, type is std::vector<int>
        """
    def rotation(self) -> float:
        """
        get rotation of BarCode
        
        Returns: return rotation of the BarCode, type is float. FIXME: always return 0.0
        """
    def type(self) -> int:
        """
        get type of BarCode
        
        Returns: return type of the BarCode, type is int
        """
    def w(self) -> int:
        """
        get w of BarCode
        
        Returns: return w of the BarCode, type is int
        """
    def x(self) -> int:
        """
        get x of BarCode
        
        Returns: return x of the BarCode, type is int
        """
    def y(self) -> int:
        """
        get y of BarCode
        
        Returns: return y of the BarCode, type is int
        """
class Blob:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] Returns the blob’s bounding box x coordinate
        [1] Returns the blob’s bounding box y coordinate
        [2] Returns the blob’s bounding box w coordinate
        [3] Returns the blob’s bounding box h coordinate
        [4] Returns the number of pixels that are part of this blob
        [5] Returns the centroid x position of the blob
        [6] Returns the centroid y position of the blob
        
        
        Returns: int& width or height
        """
    def __init__(self, rect: list[int], corners: list[list[int]], mini_corners: list[list[int]], cx: float, cy: float, pixels: int, rotation: float, code: int, count: int, perimeter: int, roundness: float, x_hist_bins: list[int], y_hist_bins: list[int]) -> None:
        ...
    def area(self) -> int:
        """
        get blob area
        
        Returns: Returns the area of the bounding box around the blob
        """
    def code(self) -> int:
        """
        get blob code
        
        Returns: Returns a 32-bit binary number with a bit set in it for each color threshold that’s part of this blob
        """
    def compactness(self) -> float:
        """
        get blob compactness
        
        Returns: Returns the compactness ratio of the blob
        """
    def convexity(self) -> float:
        """
        get blob convexity
        
        Returns: Returns a value between 0 and 1 representing how convex the object is
        """
    def corners(self) -> list[list[int]]:
        """
        get blob corners
        
        Returns: Returns a list of 4 (x,y) tuples of the 4 corners of the object.
        (x0, y0)___________(x1, y1)
        |           |
        |           |
        |           |
        |___________|
        (x3, y3)           (x2, y2)
        note: the order of corners may change
        """
    def count(self) -> int:
        """
        get blob count
        
        Returns: Returns the number of blobs merged into this blob.
        """
    def cx(self) -> int:
        """
        get blob center x
        
        Returns: Returns the centroid x position of the blob
        """
    def cxf(self) -> float:
        """
        get blob center x
        
        Returns: Returns the centroid x position of the blob
        """
    def cy(self) -> int:
        """
        get blob center y
        
        Returns: Returns the centroid y position of the blob
        """
    def cyf(self) -> float:
        """
        get blob center y
        
        Returns: Returns the centroid y position of the blob
        """
    def density(self) -> float:
        """
        get blob density
        
        Returns: Returns the density ratio of the blob
        """
    def elongation(self) -> float:
        """
        get blob elongation
        """
    def enclosed_ellipse(self) -> list[int]:
        """
        get blob enclosed_ellipse
        
        Returns: Returns an ellipse tuple (x, y, rx, ry, rotation) of the ellipse that fits inside of the min area rectangle of a blob.
        """
    def enclosing_circle(self) -> list[int]:
        """
        get blob enclosing_circle
        
        Returns: Returns a circle tuple (x, y, r) of the circle that encloses the min area rectangle of a blob.
        """
    def extent(self) -> float:
        """
        Alias for blob.density()
        
        Returns: Returns the density ratio of the blob
        """
    def h(self) -> int:
        """
        get blob height
        
        Returns: Returns the blob’s bounding box h coordinate
        """
    def major_axis_line(self) -> list[int]:
        """
        get blob major_axis_line
        
        Returns: Returns a line tuple (x1, y1, x2, y2) of the minor axis of the blob.
        """
    def mini_corners(self) -> list[list[int]]:
        """
        get blob mini corners
        
        Returns: Returns a list of 4 (x,y) tuples of the 4 corners than bound the min area rectangle of the blob.
        (x0, y0)___________(x1, y1)
        |           |
        |           |
        |           |
        |___________|
        (x3, y3)           (x2, y2)
        note: the order of corners may change
        """
    def minor_axis_line(self) -> list[int]:
        """
        get blob minor_axis_line
        
        Returns: Returns a line tuple (x1, y1, x2, y2) of the minor axis of the blob.
        """
    def perimeter(self) -> int:
        """
        get blob merge_cnt
        
        Returns: Returns the number of pixels on this blob’s perimeter.
        """
    def pixels(self) -> int:
        """
        get blob pixels
        
        Returns: Returns the number of pixels that are part of this blob.
        """
    def rect(self) -> list[int]:
        """
        get blob rect
        
        Returns: Returns the center coordinates and width and height of the rectangle. format is (x, y, w, h)
        w
        (x, y) ___________
        |           |
        |           |  h
        |           |
        |___________|
        """
    def rotation(self) -> float:
        """
        get blob rotation
        
        Returns: Returns the rotation of the blob in radians (float). If the blob is like a pencil or pen this value will be unique for 0-180 degrees.
        """
    def rotation_deg(self) -> int:
        """
        get blob rotation_deg
        
        Returns: Returns the rotation of the blob in degrees.
        """
    def rotation_rad(self) -> float:
        """
        get blob rotation_rad
        
        Returns: Returns the rotation of the blob in radians
        """
    def roundness(self) -> float:
        """
        get blob roundness
        
        Returns: Returns a value between 0 and 1 representing how round the object is
        """
    def solidity(self) -> float:
        """
        get blob solidity
        
        Returns: Returns the solidity ratio of the blob
        """
    def w(self) -> int:
        """
        get blob width
        
        Returns: Returns the blob’s bounding box w coordinate
        """
    def x(self) -> int:
        """
        get blob x of the upper left coordinate
        
        Returns: Returns the x coordinate of the upper left corner of the rectangle.
        """
    def x_hist_bins(self) -> list[int]:
        """
        get blob x_hist_bins
        
        Returns: Returns the x_hist_bins of the blob
        """
    def y(self) -> int:
        """
        get blob y of the upper left coordinate
        
        Returns: Returns the y coordinate of the upper left corner of the rectangle.
        """
    def y_hist_bins(self) -> list[int]:
        """
        get blob y_hist_bins
        
        Returns: Returns the y_hist_bins of the blob
        """
class CMap:
    """
    Members:
    
      TURBO
    
      VIRIDIS
    
      INFERNO
    
      PLASMA
    
      CIVIDIS
    
      CUBEHELIX
    
      MAGMA
    
      TWILIGHT
    
      TWILIGHT_SHIFTED
    
      GREYS
    
      JET
    
      COOLWARM
    
      RDYBU
    
      SET1
    
      TAB10
    
      TAB20
    
      THERMAL_WHITE_HOT
    
      THERMAL_BLACK_HOT
    
      THERMAL_RED_HOT
    
      THERMAL_WHITE_HOT_SD
    
      THERMAL_BLACK_HOT_SD
    
      THERMAL_RED_HOT_SD
    
      THERMAL_IRONBOW
    
      THERMAL_NIGHT
    
      GITHUB_GREEN
    
      MAX
    """
    CIVIDIS: typing.ClassVar[CMap]  # value = <CMap.CIVIDIS: 4>
    COOLWARM: typing.ClassVar[CMap]  # value = <CMap.COOLWARM: 11>
    CUBEHELIX: typing.ClassVar[CMap]  # value = <CMap.CUBEHELIX: 5>
    GITHUB_GREEN: typing.ClassVar[CMap]  # value = <CMap.GITHUB_GREEN: 24>
    GREYS: typing.ClassVar[CMap]  # value = <CMap.GREYS: 9>
    INFERNO: typing.ClassVar[CMap]  # value = <CMap.INFERNO: 2>
    JET: typing.ClassVar[CMap]  # value = <CMap.JET: 10>
    MAGMA: typing.ClassVar[CMap]  # value = <CMap.MAGMA: 6>
    MAX: typing.ClassVar[CMap]  # value = <CMap.MAX: 25>
    PLASMA: typing.ClassVar[CMap]  # value = <CMap.PLASMA: 3>
    RDYBU: typing.ClassVar[CMap]  # value = <CMap.RDYBU: 12>
    SET1: typing.ClassVar[CMap]  # value = <CMap.SET1: 13>
    TAB10: typing.ClassVar[CMap]  # value = <CMap.TAB10: 14>
    TAB20: typing.ClassVar[CMap]  # value = <CMap.TAB20: 15>
    THERMAL_BLACK_HOT: typing.ClassVar[CMap]  # value = <CMap.THERMAL_BLACK_HOT: 17>
    THERMAL_BLACK_HOT_SD: typing.ClassVar[CMap]  # value = <CMap.THERMAL_BLACK_HOT_SD: 20>
    THERMAL_IRONBOW: typing.ClassVar[CMap]  # value = <CMap.THERMAL_IRONBOW: 22>
    THERMAL_NIGHT: typing.ClassVar[CMap]  # value = <CMap.THERMAL_NIGHT: 23>
    THERMAL_RED_HOT: typing.ClassVar[CMap]  # value = <CMap.THERMAL_RED_HOT: 18>
    THERMAL_RED_HOT_SD: typing.ClassVar[CMap]  # value = <CMap.THERMAL_RED_HOT_SD: 21>
    THERMAL_WHITE_HOT: typing.ClassVar[CMap]  # value = <CMap.THERMAL_WHITE_HOT: 16>
    THERMAL_WHITE_HOT_SD: typing.ClassVar[CMap]  # value = <CMap.THERMAL_WHITE_HOT_SD: 19>
    TURBO: typing.ClassVar[CMap]  # value = <CMap.TURBO: 0>
    TWILIGHT: typing.ClassVar[CMap]  # value = <CMap.TWILIGHT: 7>
    TWILIGHT_SHIFTED: typing.ClassVar[CMap]  # value = <CMap.TWILIGHT_SHIFTED: 8>
    VIRIDIS: typing.ClassVar[CMap]  # value = <CMap.VIRIDIS: 1>
    __members__: typing.ClassVar[dict[str, CMap]]  # value = {'TURBO': <CMap.TURBO: 0>, 'VIRIDIS': <CMap.VIRIDIS: 1>, 'INFERNO': <CMap.INFERNO: 2>, 'PLASMA': <CMap.PLASMA: 3>, 'CIVIDIS': <CMap.CIVIDIS: 4>, 'CUBEHELIX': <CMap.CUBEHELIX: 5>, 'MAGMA': <CMap.MAGMA: 6>, 'TWILIGHT': <CMap.TWILIGHT: 7>, 'TWILIGHT_SHIFTED': <CMap.TWILIGHT_SHIFTED: 8>, 'GREYS': <CMap.GREYS: 9>, 'JET': <CMap.JET: 10>, 'COOLWARM': <CMap.COOLWARM: 11>, 'RDYBU': <CMap.RDYBU: 12>, 'SET1': <CMap.SET1: 13>, 'TAB10': <CMap.TAB10: 14>, 'TAB20': <CMap.TAB20: 15>, 'THERMAL_WHITE_HOT': <CMap.THERMAL_WHITE_HOT: 16>, 'THERMAL_BLACK_HOT': <CMap.THERMAL_BLACK_HOT: 17>, 'THERMAL_RED_HOT': <CMap.THERMAL_RED_HOT: 18>, 'THERMAL_WHITE_HOT_SD': <CMap.THERMAL_WHITE_HOT_SD: 19>, 'THERMAL_BLACK_HOT_SD': <CMap.THERMAL_BLACK_HOT_SD: 20>, 'THERMAL_RED_HOT_SD': <CMap.THERMAL_RED_HOT_SD: 21>, 'THERMAL_IRONBOW': <CMap.THERMAL_IRONBOW: 22>, 'THERMAL_NIGHT': <CMap.THERMAL_NIGHT: 23>, 'GITHUB_GREEN': <CMap.GITHUB_GREEN: 24>, 'MAX': <CMap.MAX: 25>}
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
class Circle:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] get x of circle
        [1] get y of circle
        [2] get r of circle
        [3] get magnitude of the circle after Hough transformation
        
        
        Returns: int&
        """
    def __init__(self, x: int, y: int, r: int, magnitude: int) -> None:
        ...
    def magnitude(self) -> int:
        """
        get magnitude of the circle after Hough transformation
        
        Returns: return magnitude, type is int
        """
    def r(self) -> int:
        """
        get r of circle
        
        Returns: return r of the circle, type is int
        """
    def x(self) -> int:
        """
        get x of circle
        
        Returns: return x of the circle, type is int
        """
    def y(self) -> int:
        """
        get y of circle
        
        Returns: return y of the circle, type is int
        """
class Color:
    alpha: float
    b: int
    format: Format
    g: int
    gray: int
    r: int
    @staticmethod
    def from_bgr(b: int, g: int, r: int) -> Color:
        """
        Create Color object from BGR channels
        """
    @staticmethod
    def from_bgra(b: int, g: int, r: int, alpha: float) -> Color:
        """
        Create Color object from BGRA channels
        
        Args:
          - alpha: alpha channel, float value, value range: 0 ~ 1
        """
    @staticmethod
    def from_gray(gray: int) -> Color:
        """
        Create Color object from gray channel
        """
    @staticmethod
    def from_hex(hex: int, format: Format) -> Color:
        """
        Create Color object from hex value
        
        Args:
          - hex: hex value, e.g. 0x0000FF00, lower address if first channel
          - format: color format, @see image::Format
        """
    @staticmethod
    def from_rgb(r: int, g: int, b: int) -> Color:
        """
        Create Color object from RGB channels
        """
    @staticmethod
    def from_rgba(r: int, g: int, b: int, alpha: float) -> Color:
        """
        Create Color object from RGBA channels
        
        Args:
          - alpha: alpha channel, float value, value range: 0 ~ 1
        """
    def __init__(self, ch1: int, ch2: int = 0, ch3: int = 0, alpha: float = 0, format: Format = ...) -> None:
        ...
    def hex(self) -> int:
        """
        Get color's hex value
        """
    def to_format(self, format: Format) -> None:
        """
        Convert Color format
        
        Args:
          - format: format want to convert to, @see image::Format, only support RGB888, BGR888, RGBA8888, BGRA8888, GRAYSCALE.
        """
    def to_format2(self, format: Format) -> Color:
        """
        Convert color format and return a new Color object
        
        Args:
          - format: format want to convert to, @see image::Format, only support RGB888, BGR888, RGBA8888, BGRA8888, GRAYSCALE.
        
        
        Returns: new Color object, you need to delete it manually in C++.
        """
class CornerDetector:
    """
    Members:
    
      CORNER_FAST
    
      CORNER_AGAST
    """
    CORNER_AGAST: typing.ClassVar[CornerDetector]  # value = <CornerDetector.CORNER_AGAST: 1>
    CORNER_FAST: typing.ClassVar[CornerDetector]  # value = <CornerDetector.CORNER_FAST: 0>
    __members__: typing.ClassVar[dict[str, CornerDetector]]  # value = {'CORNER_FAST': <CornerDetector.CORNER_FAST: 0>, 'CORNER_AGAST': <CornerDetector.CORNER_AGAST: 1>}
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
class DataMatrix:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] get x of DataMatrix
        [1] get y of DataMatrix
        [2] get w of DataMatrix
        [3] get h of DataMatrix
        [4] Not support this index, try to use payload() method
        [5] Not support this index, try to use rotation() method
        [6] get rows of DataMatrix
        [7] get columns of DataMatrix
        [8] get capacity of DataMatrix
        [9] get padding of DataMatrix
        
        
        Returns: int&
        """
    def __init__(self, rect: list[int], corners: list[list[int]], payload: str, rotation: float, rows: int, columns: int, capacity: int, padding: int) -> None:
        ...
    def capacity(self) -> int:
        """
        get capacity of DataMatrix
        
        Returns: returns how many characters could fit in this data matrix, type is int
        """
    def columns(self) -> int:
        """
        get columns of DataMatrix
        
        Returns: return columns of the DataMatrix, type is int
        """
    def corners(self) -> list[list[int]]:
        """
        get coordinate of DataMatrix
        
        Returns: return the coordinate of the DataMatrix.
        """
    def h(self) -> int:
        """
        get h of DataMatrix
        
        Returns: return h of the DataMatrix, type is int
        """
    def padding(self) -> int:
        """
        get padding of DataMatrix
        
        Returns: returns how many unused characters are in this data matrix, type is int
        """
    def payload(self) -> str:
        """
        get payload of DataMatrix
        
        Returns: return payload of the DataMatrix, type is std::string
        """
    def rect(self) -> list[int]:
        """
        get rectangle of DataMatrix
        
        Returns: return the rectangle of the DataMatrix. format is {x, y, w, h}, type is std::vector<int>
        """
    def rotation(self) -> float:
        """
        get rotation of DataMatrix
        
        Returns: return rotation of the DataMatrix, type is float
        """
    def rows(self) -> int:
        """
        get rows of DataMatrix
        
        Returns: return rows of the DataMatrix, type is int
        """
    def w(self) -> int:
        """
        get w of DataMatrix
        
        Returns: return w of the DataMatrix, type is int
        """
    def x(self) -> int:
        """
        get x of DataMatrix
        
        Returns: return x of the DataMatrix, type is int
        """
    def y(self) -> int:
        """
        get y of DataMatrix
        
        Returns: return y of the DataMatrix, type is int
        """
class Displacement:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: array index
        
        
        Returns: int&
        """
    def __init__(self, x_translation: float, y_translation: float, rotation: float, scale: float, response: float) -> None:
        ...
    def response(self) -> float:
        """
        get response of Displacement
        
        Returns: return response of the Displacement, type is float
        """
    def rotation(self) -> float:
        """
        get rotation of Displacement
        
        Returns: return rotation of the Displacement, type is float
        """
    def scale(self) -> float:
        """
        get scale of Displacement
        
        Returns: return scale of the Displacement, type is float
        """
    def x_translation(self) -> float:
        """
        get x_translation of Displacement
        
        Returns: return x_translation of the Displacement, type is float
        """
    def y_translation(self) -> float:
        """
        get y_translation of Displacement
        
        Returns: return y_translation of the Displacement, type is float
        """
class EdgeDetector:
    """
    Members:
    
      EDGE_CANNY
    
      EDGE_SIMPLE
    """
    EDGE_CANNY: typing.ClassVar[EdgeDetector]  # value = <EdgeDetector.EDGE_CANNY: 0>
    EDGE_SIMPLE: typing.ClassVar[EdgeDetector]  # value = <EdgeDetector.EDGE_SIMPLE: 1>
    __members__: typing.ClassVar[dict[str, EdgeDetector]]  # value = {'EDGE_CANNY': <EdgeDetector.EDGE_CANNY: 0>, 'EDGE_SIMPLE': <EdgeDetector.EDGE_SIMPLE: 1>}
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
class Fit:
    """
    Members:
    
      FIT_NONE
    
      FIT_FILL
    
      FIT_CONTAIN
    
      FIT_COVER
    
      FIT_MAX
    """
    FIT_CONTAIN: typing.ClassVar[Fit]  # value = <Fit.FIT_CONTAIN: 1>
    FIT_COVER: typing.ClassVar[Fit]  # value = <Fit.FIT_COVER: 2>
    FIT_FILL: typing.ClassVar[Fit]  # value = <Fit.FIT_FILL: 0>
    FIT_MAX: typing.ClassVar[Fit]  # value = <Fit.FIT_MAX: 3>
    FIT_NONE: typing.ClassVar[Fit]  # value = <Fit.FIT_NONE: -1>
    __members__: typing.ClassVar[dict[str, Fit]]  # value = {'FIT_NONE': <Fit.FIT_NONE: -1>, 'FIT_FILL': <Fit.FIT_FILL: 0>, 'FIT_CONTAIN': <Fit.FIT_CONTAIN: 1>, 'FIT_COVER': <Fit.FIT_COVER: 2>, 'FIT_MAX': <Fit.FIT_MAX: 3>}
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
class FlipDir:
    """
    Members:
    
      X
    
      Y
    
      XY
    """
    X: typing.ClassVar[FlipDir]  # value = <FlipDir.X: 0>
    XY: typing.ClassVar[FlipDir]  # value = <FlipDir.XY: 2>
    Y: typing.ClassVar[FlipDir]  # value = <FlipDir.Y: 1>
    __members__: typing.ClassVar[dict[str, FlipDir]]  # value = {'X': <FlipDir.X: 0>, 'Y': <FlipDir.Y: 1>, 'XY': <FlipDir.XY: 2>}
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
class Format:
    """
    Members:
    
      FMT_RGB888
    
      FMT_BGR888
    
      FMT_RGBA8888
    
      FMT_BGRA8888
    
      FMT_RGB565
    
      FMT_BGR565
    
      FMT_YUV422SP
    
      FMT_YUV422P
    
      FMT_YVU420SP
    
      FMT_YUV420SP
    
      FMT_YVU420P
    
      FMT_YUV420P
    
      FMT_GRAYSCALE
    
      FMT_BGGR6
    
      FMT_GBRG6
    
      FMT_GRBG6
    
      FMT_RGGB6
    
      FMT_BGGR8
    
      FMT_GBRG8
    
      FMT_GRBG8
    
      FMT_RGGB8
    
      FMT_BGGR10
    
      FMT_GBRG10
    
      FMT_GRBG10
    
      FMT_RGGB10
    
      FMT_BGGR12
    
      FMT_GBRG12
    
      FMT_GRBG12
    
      FMT_RGGB12
    
      FMT_UNCOMPRESSED_MAX
    
      FMT_COMPRESSED_MIN
    
      FMT_JPEG
    
      FMT_PNG
    
      FMT_COMPRESSED_MAX
    
      FMT_INVALID
    """
    FMT_BGGR10: typing.ClassVar[Format]  # value = <Format.FMT_BGGR10: 21>
    FMT_BGGR12: typing.ClassVar[Format]  # value = <Format.FMT_BGGR12: 25>
    FMT_BGGR6: typing.ClassVar[Format]  # value = <Format.FMT_BGGR6: 13>
    FMT_BGGR8: typing.ClassVar[Format]  # value = <Format.FMT_BGGR8: 17>
    FMT_BGR565: typing.ClassVar[Format]  # value = <Format.FMT_BGR565: 5>
    FMT_BGR888: typing.ClassVar[Format]  # value = <Format.FMT_BGR888: 1>
    FMT_BGRA8888: typing.ClassVar[Format]  # value = <Format.FMT_BGRA8888: 3>
    FMT_COMPRESSED_MAX: typing.ClassVar[Format]  # value = <Format.FMT_COMPRESSED_MAX: 33>
    FMT_COMPRESSED_MIN: typing.ClassVar[Format]  # value = <Format.FMT_COMPRESSED_MIN: 30>
    FMT_GBRG10: typing.ClassVar[Format]  # value = <Format.FMT_GBRG10: 22>
    FMT_GBRG12: typing.ClassVar[Format]  # value = <Format.FMT_GBRG12: 26>
    FMT_GBRG6: typing.ClassVar[Format]  # value = <Format.FMT_GBRG6: 14>
    FMT_GBRG8: typing.ClassVar[Format]  # value = <Format.FMT_GBRG8: 18>
    FMT_GRAYSCALE: typing.ClassVar[Format]  # value = <Format.FMT_GRAYSCALE: 12>
    FMT_GRBG10: typing.ClassVar[Format]  # value = <Format.FMT_GRBG10: 23>
    FMT_GRBG12: typing.ClassVar[Format]  # value = <Format.FMT_GRBG12: 27>
    FMT_GRBG6: typing.ClassVar[Format]  # value = <Format.FMT_GRBG6: 15>
    FMT_GRBG8: typing.ClassVar[Format]  # value = <Format.FMT_GRBG8: 19>
    FMT_INVALID: typing.ClassVar[Format]  # value = <Format.FMT_INVALID: 255>
    FMT_JPEG: typing.ClassVar[Format]  # value = <Format.FMT_JPEG: 31>
    FMT_PNG: typing.ClassVar[Format]  # value = <Format.FMT_PNG: 32>
    FMT_RGB565: typing.ClassVar[Format]  # value = <Format.FMT_RGB565: 4>
    FMT_RGB888: typing.ClassVar[Format]  # value = <Format.FMT_RGB888: 0>
    FMT_RGBA8888: typing.ClassVar[Format]  # value = <Format.FMT_RGBA8888: 2>
    FMT_RGGB10: typing.ClassVar[Format]  # value = <Format.FMT_RGGB10: 24>
    FMT_RGGB12: typing.ClassVar[Format]  # value = <Format.FMT_RGGB12: 28>
    FMT_RGGB6: typing.ClassVar[Format]  # value = <Format.FMT_RGGB6: 16>
    FMT_RGGB8: typing.ClassVar[Format]  # value = <Format.FMT_RGGB8: 20>
    FMT_UNCOMPRESSED_MAX: typing.ClassVar[Format]  # value = <Format.FMT_UNCOMPRESSED_MAX: 29>
    FMT_YUV420P: typing.ClassVar[Format]  # value = <Format.FMT_YUV420P: 11>
    FMT_YUV420SP: typing.ClassVar[Format]  # value = <Format.FMT_YUV420SP: 9>
    FMT_YUV422P: typing.ClassVar[Format]  # value = <Format.FMT_YUV422P: 7>
    FMT_YUV422SP: typing.ClassVar[Format]  # value = <Format.FMT_YUV422SP: 6>
    FMT_YVU420P: typing.ClassVar[Format]  # value = <Format.FMT_YVU420P: 10>
    FMT_YVU420SP: typing.ClassVar[Format]  # value = <Format.FMT_YVU420SP: 8>
    __members__: typing.ClassVar[dict[str, Format]]  # value = {'FMT_RGB888': <Format.FMT_RGB888: 0>, 'FMT_BGR888': <Format.FMT_BGR888: 1>, 'FMT_RGBA8888': <Format.FMT_RGBA8888: 2>, 'FMT_BGRA8888': <Format.FMT_BGRA8888: 3>, 'FMT_RGB565': <Format.FMT_RGB565: 4>, 'FMT_BGR565': <Format.FMT_BGR565: 5>, 'FMT_YUV422SP': <Format.FMT_YUV422SP: 6>, 'FMT_YUV422P': <Format.FMT_YUV422P: 7>, 'FMT_YVU420SP': <Format.FMT_YVU420SP: 8>, 'FMT_YUV420SP': <Format.FMT_YUV420SP: 9>, 'FMT_YVU420P': <Format.FMT_YVU420P: 10>, 'FMT_YUV420P': <Format.FMT_YUV420P: 11>, 'FMT_GRAYSCALE': <Format.FMT_GRAYSCALE: 12>, 'FMT_BGGR6': <Format.FMT_BGGR6: 13>, 'FMT_GBRG6': <Format.FMT_GBRG6: 14>, 'FMT_GRBG6': <Format.FMT_GRBG6: 15>, 'FMT_RGGB6': <Format.FMT_RGGB6: 16>, 'FMT_BGGR8': <Format.FMT_BGGR8: 17>, 'FMT_GBRG8': <Format.FMT_GBRG8: 18>, 'FMT_GRBG8': <Format.FMT_GRBG8: 19>, 'FMT_RGGB8': <Format.FMT_RGGB8: 20>, 'FMT_BGGR10': <Format.FMT_BGGR10: 21>, 'FMT_GBRG10': <Format.FMT_GBRG10: 22>, 'FMT_GRBG10': <Format.FMT_GRBG10: 23>, 'FMT_RGGB10': <Format.FMT_RGGB10: 24>, 'FMT_BGGR12': <Format.FMT_BGGR12: 25>, 'FMT_GBRG12': <Format.FMT_GBRG12: 26>, 'FMT_GRBG12': <Format.FMT_GRBG12: 27>, 'FMT_RGGB12': <Format.FMT_RGGB12: 28>, 'FMT_UNCOMPRESSED_MAX': <Format.FMT_UNCOMPRESSED_MAX: 29>, 'FMT_COMPRESSED_MIN': <Format.FMT_COMPRESSED_MIN: 30>, 'FMT_JPEG': <Format.FMT_JPEG: 31>, 'FMT_PNG': <Format.FMT_PNG: 32>, 'FMT_COMPRESSED_MAX': <Format.FMT_COMPRESSED_MAX: 33>, 'FMT_INVALID': <Format.FMT_INVALID: 255>}
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
class HaarCascade:
    def __init__(self) -> None:
        ...
class Histogram:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        """
    def __init__(self, l_bin: list[float], a_bin: list[float], b_bin: list[float], format: Format = ...) -> None:
        ...
    def a_bins(self) -> list[float]:
        """
        Returns a list of floats for the RGB565 histogram LAB A channel.
        """
    def b_bins(self) -> list[float]:
        """
        Returns a list of floats for the RGB565 histogram LAB B channel.
        """
    def bins(self) -> list[float]:
        """
        Returns a list of floats for the grayscale histogram.
        """
    def get_percentile(self, percentile: float) -> Percentile:
        """
        Computes the CDF of the histogram channels and returns a image::Percentile object
        
        Args:
          - percentile: the values of the histogram at the passed in percentile (0.0 - 1.0) (float).
        So, if you pass in 0.1 this method will tell you (going from left-to-right in the histogram)
        what bin when summed into an accumulator caused the accumulator to cross 0.1. This is useful
        to determine min (with 0.1) and max (with 0.9) of a color distribution without outlier effects
        ruining your results for adaptive color tracking.
        
        
        Returns: image::Percentile object
        """
    def get_statistics(self) -> Statistics:
        """
        Computes the mean, median, mode, standard deviation, min, max, lower quartile, and upper quartile of each color channel in the histogram and returns a image::Statistics object.
        
        Returns: image::Statistics object
        """
    def get_threshold(self) -> Threshold:
        """
        Uses Otsu’s Method to compute the optimal threshold values that split the histogram into two halves for each channel of the histogram and returns a image::Threshold object.
        
        Returns: image::Threshold object
        """
    def l_bins(self) -> list[float]:
        """
        Returns a list of floats for the RGB565 histogram LAB L channel.
        """
class Image:
    @staticmethod
    def to_bytes(*args, **kwargs):
        """
        Get image's data and convert to array bytes
        
        Args:
          - copy: if true, will alloc memory and copy data to new buffer,
        else will use the memory of Image object, delete bytes object will not affect Image object，
        but delete Image object will make bytes object invalid, it may cause program crash !!!!
        So use this param carefully.
        
        
        Returns: image's data bytes, need be delete by caller in C++.
        """
    def __init__(self, width: int, height: int, format: Format = ..., bg: Color = ...) -> None:
        ...
    def __str__(self) -> str:
        """
        To string method
        """
    def add(self, other: Image, mask: Image = None) -> Image:
        """
        Adds the other image to the image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.    TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def affine(self, src_points: list[int], dst_points: list[int], width: int = -1, height: int = -1, method: ResizeMethod = ...) -> Image:
        """
        Affine transform image, will create a new transformed image object, need 3 points.
        
        Args:
          - src_points: three source points, [x1, y1, x2, y2, x3, y3]
          - dst_points: three destination points, [x1, y1, x2, y2, x3, y3]
          - width: new width, if value is -1, will use height to calculate aspect ratio
          - height: new height, if value is -1, will use width to calculate aspect ratio
          - method: resize method, by default is bilinear
        
        
        Returns: new transformed image object
        """
    def awb(self, max: bool = False) -> Image:
        """
        Performs an auto white balance operation on the image. TODO: support in the future
        
        Args:
          - max: if True uses the white-patch algorithm instead. default is false.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_and(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise and operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_nand(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise nand operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_nor(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise nor operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_or(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise or operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_xnor(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise xnor operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def b_xor(self, other: Image, mask: Image = None) -> Image:
        """
        Performs a bitwise xor operation between the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.        TODO: support path?
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def bilateral(self, size: int, color_sigma: float = 0.1, space_sigma: float = 1, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Convolves the image by a bilateral filter.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - color_sigma: Controls how closely colors are matched using the bilateral filter. default is 0.1.
          - space_sigma: Controls how closely pixels space-wise are blurred with each other. default is 1.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def binary(self, thresholds: list[list[int]] = [], invert: bool = False, zero: bool = False, mask: Image = None, to_bitmap: bool = False, copy: bool = False) -> Image:
        """
        Sets all pixels in the image to black or white depending on if the pixel is inside of a threshold in the threshold list thresholds or not.
        
        Args:
          - thresholds: You can define multiple thresholds.
        For GRAYSCALE format, you can use {{Lmin, Lmax}, ...} to define one or more thresholds.
        For RGB888 format, you can use {{Lmin, Lmax, Amin, Amax, Bmin, Bmax}, ...} to define one or more thresholds.
        Where the upper case L,A,B represent the L,A,B channels of the LAB image format, and min, max represent the minimum and maximum values of the corresponding channels.
          - invert: If true, the thresholds will be inverted before the operation. default is false.
          - zero: If zero is true, the image will be set the pixels within the threshold to 0, other pixels remain unchanged. If zero is false, the image will be set to black or white. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
          - to_bitmap: If true, the image will be converted to a bitmap image before thresholding. default is false. TODO: support in the future
          - copy: Select whether to return a new image or modify the original image. default is false.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def black_hat(self, size: int, threshold: int = 0, mask: Image = None) -> Image:
        """
        Returns the image difference of the image and Image.close()’ed image.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: As the threshold for close method. default is 0.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def blend(self, other: Image, alpha: int = 128, mask: Image = None) -> Image:
        """
        Blends the image with the other image.
        res = alpha * this_img / 256 + (256 - alpha) * other_img / 256
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - alpha: The alpha value of the blend, the value range is [0, 256],default is 128.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def ccm(self, matrix: list[float]) -> Image:
        """
        Multiples the passed (3x3) or (4x3) floating-point color-correction-matrix with the image.
        note: Grayscale format is not support.
        
        Args:
          - matrix: The color correction matrix to use. 3x3 or 4x3 matrix.
        Weights may either be positive or negative, and the sum of each column in the 3x3 matrix should generally be 1.
        example:
        {
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
        }
        Where the last row of the 4x3 matrix is an offset per color channel. If you add an offset you may wish to make the
        weights sum to less than 1 to account for the offset.
        example:
        {
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
        0, 0, 0,
        }
        
        
        Returns: Returns the image after the operation is completed.
        """
    def clear(self, mask: Image = None) -> Image:
        """
        Sets all pixels in the image to zero
        
        Args:
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def close(self, size: int, threshold: int = 0, mask: Image = None) -> Image:
        """
        Performs dilation and erosion on an image in order.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: As the threshold for erosion and dilation, the actual threshold for erosion is (kernel_size - 1 - threshold), the actual threshold for dialation is threshold. default is 0.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def compress(self, quality: int = 95) -> Image:
        """
        JPEG compresses the image in place, the same as to_jpeg functioin, it's recommend to use to_jpeg instead.
        
        Args:
          - quality: The quality of the compressed image. default is 95.
        
        
        Returns: Returns the compressed JPEG image
        """
    def copy(self) -> Image:
        """
        Copy image, will create a new copied image object
        
        Returns: new copied image object
        """
    def crop(self, x: int, y: int, w: int, h: int) -> Image:
        """
        Crop image, will create a new cropped image object
        
        Args:
          - x: left top corner of crop rectangle point's coordinate x
          - y: left top corner of crop rectangle point's coordinate y
          - w: crop rectangle width
          - h: crop rectangle height
        
        
        Returns: new cropped image object
        """
    def data_size(self) -> int:
        """
        Get image's data size
        """
    def difference(self, other: Image, mask: Image = None) -> Image:
        """
        Caculate the absolute value of the difference between each pixel in the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def dilate(self, size: int, threshold: int = 0, mask: Image = None) -> Image:
        """
        Dilates the image in place.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: The number of pixels in the kernel that are not 0. If it is greater than or equal to the threshold, set the center pixel to white. default is 0.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def div(self, other: Image, invert: bool = False, mod: bool = False, mask: Image = None) -> Image:
        """
        Divides the image by the other image.
        This method is meant for image blending and cannot divide the pixels in the image by a scalar like 2.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.    TODO: support path?
          - invert: If true, the image will be change the division direction from a/b to b/a. default is false.
          - mod: If true, the image will be change the division operation to the modulus operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def draw_arrow(self, x0: int, y0: int, x1: int, y1: int, color: Color, thickness: int = 1) -> Image:
        """
        Draw arrow on image
        
        Args:
          - x0: start coordinate of the arrow x0
          - y0: start coordinate of the arrow y0
          - x1: end coordinate of the arrow x1
          - y1: end coordinate of the arrow y1
          - color: cross color @see image::Color
          - thickness: cross thickness(line width), by default(value is 1)
        
        
        Returns: this image object self
        """
    def draw_circle(self, x: int, y: int, radius: int, color: Color, thickness: int = 1) -> Image:
        """
        Draw circle on image
        
        Args:
          - x: circle center point's coordinate x
          - y: circle center point's coordinate y
          - radius: circle radius
          - color: circle color @see image::Color
          - thickness: circle thickness(line width), default -1 means fill circle
        
        
        Returns: this image object self
        """
    def draw_cross(self, x: int, y: int, color: Color, size: int = 5, thickness: int = 1) -> Image:
        """
        Draw cross on image
        
        Args:
          - x: cross center point's coordinate x
          - y: cross center point's coordinate y
          - color: cross color @see image::Color
          - size: how long the lines of the cross extend, by default(value is 5). So the line length is `2 * size + thickness`
          - thickness: cross thickness(line width), by default(value is 1)
        """
    def draw_edges(self, corners: list[list[int]], color: Color, size: int = 0, thickness: int = 1, fill: bool = False) -> Image:
        """
        Draw edges on image
        
        Args:
          - corners: edges, [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
          - color: edges color @see image::Color
          - size: the circle of radius size. TODO: support in the future
          - thickness: edges thickness(line width), by default(value is 1)
          - fill: if true, will fill edges, by default(value is false)
        
        
        Returns: this image object self
        """
    def draw_ellipse(self, x: int, y: int, a: int, b: int, angle: float, start_angle: float, end_angle: float, color: Color, thickness: int = 1) -> Image:
        """
        Draw ellipse on image
        
        Args:
          - x: ellipse center point's coordinate x
          - y: ellipse center point's coordinate y
          - a: ellipse major axis length
          - b: ellipse minor axis length
          - angle: ellipse rotation angle
          - start_angle: ellipse start angle
          - end_angle: ellipse end angle
          - color: ellipse color @see image::Color
          - thickness: ellipse thickness(line width), by default(value is 1), -1 means fill ellipse
        
        
        Returns: this image object self
        """
    def draw_image(self, x: int, y: int, img: Image) -> Image:
        """
        Draw image on this image
        
        Args:
          - x: left top corner of image point's coordinate x
          - y: left top corner of image point's coordinate y
          - img: image object to draw, the caller's channel must <= the args' channel,
        e.g. caller is RGB888, args is RGBA8888, will throw exception, but caller is RGBA8888, args is RGB888 or RGBA8888 is ok
        
        
        Returns: this image object self
        """
    def draw_keypoints(self, keypoints: list[int], color: Color, size: int = 4, thickness: int = -1, line_thickness: int = 0) -> Image:
        """
        Draw keypoints on image
        
        Args:
          - keypoints: keypoints, [x1, y1, x2, y2...] or [x, y, rotation_andle_in_degrees, x2, y2, rotation_andle_in_degrees2](TODO: rotation_andle_in_degrees support in the future)
          - color: keypoints color @see image::Color
          - size: size of keypoints(radius)
          - thickness: keypoints thickness(line width), by default(value is -1 means fill circle)
          - line_thickness: line thickness, default 0 means not draw lines, > 0 will draw lines connect points.
        
        
        Returns: this image object self
        """
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: Color, thickness: int = 1) -> Image:
        """
        Draw line on image
        
        Args:
          - x1: start point's coordinate x
          - y1: start point's coordinate y
          - x2: end point's coordinate x
          - y2: end point's coordinate y
          - color: line color @see image::Color
          - thickness: line thickness(line width), by default(value is 1)
        
        
        Returns: this image object self
        """
    def draw_rect(self, x: int, y: int, w: int, h: int, color: Color, thickness: int = 1) -> Image:
        """
        Fill rectangle color to image
        
        Args:
          - x: left top corner of rectangle point's coordinate x
          - y: left top corner of rectangle point's coordinate y
          - w: rectangle width
          - h: rectangle height
          - color: rectangle color
          - thickness: rectangle thickness(line width), by default(value is 1), -1 means fill rectangle
        
        
        Returns: this image object self
        """
    def draw_string(self, x: int, y: int, textstring: str, color: Color = ..., scale: float = 1, thickness: int = -1, wrap: bool = True, wrap_space: int = 4, font: str = '') -> Image:
        """
        Draw text on image
        
        Args:
          - x: text left top point's coordinate x
          - y: text left top point's coordinate y
          - string: text content
          - color: text color @see image::Color, default is white
          - scale: font scale, by default(value is 1)
          - thickness: text thickness(line width), if negative, the glyph is filled, by default(value is -1)
          - wrap: if true, will auto wrap text to next line if text width > image width, by default(value is true)
        
        
        Returns: this image object self
        """
    def erode(self, size: int, threshold: int = -1, mask: Image = None) -> Image:
        """
        Erodes the image in place.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: The number of pixels in the kernel that are not 0. If it is less than or equal to the threshold, set the center pixel to black. default is (kernel_size - 1).
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def find_apriltags(self, roi: list[int] = [], families: ApriltagFamilies = ..., fx: float = -1, fy: float = -1, cx: int = -1, cy: int = -1) -> list[AprilTag]:
        """
        Finds all apriltags in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - families: The families to use for the apriltags. default is TAG36H11.
          - fx: The camera X focal length in pixels, default is -1.
          - fy: The camera Y focal length in pixels, default is -1.
          - cx: The camera X center in pixels, default is image.width / 2.
          - cy: The camera Y center in pixels, default is image.height / 2.
        
        
        Returns: Returns the apriltags of the image
        """
    def find_barcodes(self, roi: list[int] = []) -> list[BarCode]:
        """
        Finds all barcodes in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
        
        
        Returns: Returns the barcodes of the image
        """
    def find_blobs(self, thresholds: list[list[int]] = [], invert: bool = False, roi: list[int] = [], x_stride: int = 2, y_stride: int = 1, area_threshold: int = 10, pixels_threshold: int = 10, merge: bool = False, margin: int = 0, x_hist_bins_max: int = 0, y_hist_bins_max: int = 0) -> list[Blob]:
        """
        Finds all blobs in the image and returns a list of image.Blob class which describe each Blob.
        Please see the image.Blob object more more information.
        
        Args:
          - thresholds: You can define multiple thresholds.
        For GRAYSCALE format, you can use {{Lmin, Lmax}, ...} to define one or more thresholds.
        For RGB888 format, you can use {{Lmin, Lmax, Amin, Amax, Bmin, Bmax}, ...} to define one or more thresholds.
        Where the upper case L,A,B represent the L,A,B channels of the LAB image format, and min, max represent the minimum and maximum values of the corresponding channels.
          - invert: if true, will invert thresholds before find blobs, default is false
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - x_stride: x stride is the number of x pixels to skip when doing the hough transform. default is 2
          - y_stride: y_stride is the number of y pixels to skip when doing the hough transform. default is 1
          - area_threshold: area threshold, if the blob area is smaller than area_threshold, the blob is not returned, default is 10
          - pixels_threshold: pixels threshold, if the blob pixels is smaller than area_threshold, the blob is not returned,, default is 10.
        when x_stride and y_stride is equal to 1, pixels_threshold is equivalent to area_threshold
          - merge: if True merges all not filtered out blobs whos bounding rectangles intersect each other. default is false
          - margin: margin can be used to increase or decrease the size of the bounding rectangles for blobs during the intersection test.
        For example, with a margin of 1 blobs whos bounding rectangles are 1 pixel away from each other will be merged. default is 0
          - x_hist_bins_max: if set to non-zero populates a histogram buffer in each blob object with an x_histogram projection of all columns in the object. This value then sets the number of bins for that projection.
          - y_hist_bins_max: if set to non-zero populates a histogram buffer in each blob object with an y_histogram projection of all rows in the object. This value then sets the number of bins for that projection.
        
        
        Returns: Return the blob when found blobs, format is (blob1, blob2, ...), you can use blob class methods to do more operations.
        """
    def find_circles(self, roi: list[int] = [], x_stride: int = 2, y_stride: int = 1, threshold: int = 2000, x_margin: int = 10, y_margin: int = 10, r_margin: int = 10, r_min: int = 2, r_max: int = -1, r_step: int = 2) -> list[Circle]:
        """
        Find circles in image
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - x_stride: x stride is the number of x pixels to skip when doing the hough transform. default is 2
          - y_stride: y_stride is the number of y pixels to skip when doing the hough transform. default is 1
          - threshold: threshold controls what circles are detected from the hough transform. Only circles with a magnitude greater than or equal to threshold are returned.
        The right value of threshold for your application is image dependent.
          - x_margin: x_margin controls the merging of detected circles. Circles which are x_margin, y_margin, and r_margin pixels apart are merged. default is 10
          - y_margin: y_margin controls the merging of detected circles. Circles which are x_margin, y_margin, and r_margin pixels apart are merged. default is 10
          - r_margin: r_margin controls the merging of detected circles. Circles which are x_margin, y_margin, and r_margin pixels apart are merged. default is 10
          - r_min: r_min controls the minimum circle radius detected. Increase this to speed up the algorithm. default is 2
          - r_max: r_max controls the maximum circle radius detected. Decrease this to speed up the algorithm. default is min(roi.w / 2, roi.h / 2)
          - r_step: r_step controls how to step the radius detection by. default is 2.
        
        
        Returns: Return the circle when found circles, format is (circle1, circle2, ...), you can use circle class methods to do more operations
        """
    def find_datamatrices(self, roi: list[int] = [], effort: int = 200) -> list[DataMatrix]:
        """
        Finds all datamatrices in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - effort: Controls how much time to spend trying to find data matrix matches. default is 200.
        
        
        Returns: Returns the datamatrices of the image
        """
    def find_displacement(self, template_image: Image, roi: list[int] = [], template_roi: list[int] = [], logpolar: bool = False) -> Displacement:
        """
        Finds the displacement between the image and the template.    TODO: support in the future
        note: this method must be used on power-of-2 image sizes
        
        Args:
          - template_image: The template image.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - template_roi: The region-of-interest rectangle (x, y, w, h) to work in. If not specified, it is equal to the image rectangle.
          - logpolar: If true, it will instead find rotation and scale changes between the two images. default is false.
        
        
        Returns: Returns the displacement of the image
        """
    def find_edges(self, edge_type: EdgeDetector, roi: list[int] = [], threshold: list[int] = [100, 200]) -> Image:
        """
        Finds the edges in the image.
        
        Args:
          - edge_type: The edge type to use for the edges. default is EDGE_CANNY.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - threshold: The threshold to use for the edges. default is 20.
        
        
        Returns: Returns the edges of the image
        """
    def find_features(self, cascade: int, threshold: float = 0.5, scale: float = 1.5, roi: list[int] = []) -> list[int]:
        """
        Finds the features in the image.  TODO: support in the future
        
        Args:
          - cascade: The cascade to use for the features. default is CASCADE_FRONTALFACE_ALT.
          - threshold: The threshold to use for the features. default is 0.5.
          - scale: The scale to use for the features. default is 1.5.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
        
        
        Returns: Returns the features of the image
        """
    def find_hog(self, roi: list[int] = [], size: int = 8) -> Image:
        """
        Finds the hog in the image.   TODO: support in the future
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - size: The size to use for the hog. default is 8.
        
        
        Returns: Returns the hog of the image
        """
    def find_keypoints(self, roi: list[int] = [], threshold: int = 20, normalized: bool = False, scale_factor: float = 1.5, max_keypoints: int = 100, corner_detector: CornerDetector = ...) -> ORBKeyPoint:
        """
        Finds the keypoints in the image. TODO: support in the future.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - threshold: The threshold to use for the keypoints. default is 20.
          - normalized: If true, the image will be normalized before the operation. default is false.
          - scale_factor: The scale factor to use for the keypoints. default is 1.5.
          - max_keypoints: The maximum number of keypoints to use for the keypoints. default is 100.
          - corner_detector: The corner detector to use for the keypoints. default is CORNER_AGAST.
        
        
        Returns: Returns the keypoints of the image
        """
    def find_lbp(self, roi: list[int] = []) -> LBPKeyPoint:
        """
        Finds the lbp in the image. TODO: support in the future.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
        
        
        Returns: Returns the lbp of the image
        """
    def find_line_segments(self, roi: list[int] = [], merge_distance: int = 0, max_theta_difference: int = 15) -> list[Line]:
        """
        Finds all line segments in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - merge_distance: The maximum distance between two lines to merge them. default is 0.
          - max_theta_difference: The maximum difference between two lines to merge them. default is 15.
        
        
        Returns: Return the line when found lines, format is (line1, line2, ...), you can use line class methods to do more operations
        """
    def find_lines(self, roi: list[int] = [], x_stride: int = 2, y_stride: int = 1, threshold: float = 1000, theta_margin: float = 25, rho_margin: float = 25) -> list[Line]:
        """
        Find lines in image
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - x_stride: x stride is the number of x pixels to skip when doing the hough transform. default is 2
          - y_stride: y_stride is the number of y pixels to skip when doing the hough transform. default is 1
          - threshold: threshold threshold controls what lines are detected from the hough transform. Only lines with a magnitude greater than or equal to threshold are returned.
        The right value of threshold for your application is image dependent. default is 1000.
          - theta_margin: theta_margin controls the merging of detected lines. default is 25.
          - rho_margin: rho_margin controls the merging of detected lines. default is 25.
        
        
        Returns: Return the line when found lines, format is (line1, line2, ...), you can use line class methods to do more operations
        """
    def find_qrcodes(self, roi: list[int] = [], decoder_type: QRCodeDecoderType = ...) -> list[QRCode]:
        """
        Finds all qrcodes in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - decoder_type: Select the QR code decoding method. Choosing QRCODE_DECODER_TYPE_QUIRC allows for retrieving QR code version, ECC level, mask, data type, and other details,
        though it may decode slower at lower resolutions. Opting for QRCODE_DECODER_TYPE_ZBAR enables faster decoding at lower resolutions but may slow down at higher resolutions,
        providing only the QR code content and position information. default is QRCODE_DECODER_TYPE_ZBAR.
        Choosing the QRCODE_DECODER_TYPE_ZXING option will use the ZXing library for decoding. Supports both QRCode and Datamatrix.
        Can be used as an alternative to function find_datamatrices to decode Datamatrix codes.
        If you find that find_datamatrices is not working well for your Datamatrix codes, you can try using this option instead.
        Provides only the QR code/ datamatrix content and position information. default is QRCODE_DECODER_TYPE_ZXING.
        
        
        Returns: Returns the qrcodes / (and/or datamatrix for option ZXing) of the image
        """
    def find_rects(self, roi: list[int] = [], threshold: int = 10000) -> list[Rect]:
        """
        Finds all rects in the image.
        
        Args:
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - threshold: The threshold to use for the rects. default is 10000.
        
        
        Returns: Returns the rects of the image
        """
    def find_template(self, template_image: Image, threshold: float, roi: list[int] = [], step: int = 2, search: TemplateMatch = ...) -> list[int]:
        """
        Finds the template in the image.
        
        Args:
          - template_image: The template image.
          - threshold: Threshold is floating point number (0.0-1.0) where a higher threshold prevents false positives while lowering the detection rate while a lower threshold does the opposite.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image. Only valid in SEARCH_EX mode.
          - step: The step size to use for the template. default is 2. Only valid in SEARCH_EX mode
          - search: The search method to use for the template. default is SEARCH_EX.
        
        
        Returns: Returns a bounding box tuple (x, y, w, h) for the matching location otherwise None.
        """
    def flip(self, dir: FlipDir) -> Image:
        """
        Vertical flip image, and return a new image.
        
        Args:
          - dir: flip dir, see image.FlipDir, e.g. image.FlipDir.X is vertical flip.
        
        
        Returns: new flipped image.
        """
    def flood_fill(self, x: int, y: int, seed_threshold: float = 0.05, floating_threshold: float = 0.05, color: Color = ..., invert: bool = False, clear_background: bool = False, mask: Image = None) -> Image:
        """
        Flood fills a region of the image starting from location x, y.
        
        Args:
          - x: The x coordinate of the seed point.
          - y: The y coordinate of the seed point.
          - seed_threshold: The seed_threshold value controls how different any pixel in the fill area may be from the original starting pixel. default is 0.05.
          - floating_threshold: The floating_threshold value controls how different any pixel in the fill area may be from any neighbor pixels. default is 0.05.
          - color: The color to fill the region with. default is white.
          - invert: If true, the image will be inverted before the operation. default is false.
          - clear_background: If true, the background will be cleared before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None. FIXME: the mask image works abnormally
        
        
        Returns: Returns the image after the operation is completed.
        """
    def format(self) -> Format:
        """
        Get image's format
        """
    def gamma(self, gamma: float = 1.0, contrast: float = 1.0, brightness: float = 0.0) -> Image:
        """
        Quickly changes the image gamma, contrast, and brightness. Create a array whose size is usually 255,
        and use the parameters gamma, contrast, and brightness to calculate the value of the array, and then map the
        image pixel value through the value of the array.
        The calculation method for array is: array[array_idx] = (powf((array_idx / 255.0), (1 / gamma)) * contrast + brightness) * scale,
        `powf` is a function used to calculate floating point power.
        `array` is the array used for mapping.
        `array_idx` is the index of the array, the maximum value is determined according to the image format, usually 255.
        `scale` is a constant, the value is determined by the image format, usually 255.
        Mapping method:
        Assume that a pixel value in the image is 128, then map the pixel value to the value of array[128]
        Users can adjust the value of the array through the gamma, contrast, and brightness parameters.
        
        Args:
          - gamma: The contrast gamma greater than 1.0 makes the image darker in a non-linear manner while less than 1.0 makes the image brighter. default is 1.0.
          - contrast: The contrast value greater than 1.0 makes the image brighter in a linear manner while less than 1.0 makes the image darker. default is 1.0.
          - brightness: The brightness value greater than 0.0 makes the image brighter in a constant manner while less than 0.0 makes the image darker. default is 0.0.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def gamma_corr(self, gamma: float, contrast: float = 1.0, brightness: float = 0.0) -> Image:
        """
        Alias for Image.gamma.
        
        Args:
          - gamma: The contrast gamma greater than 1.0 makes the image darker in a non-linear manner while less than 1.0 makes the image brighter. default is 1.0.
          - contrast: The contrast value greater than 1.0 makes the image brighter in a linear manner while less than 1.0 makes the image darker. default is 1.0.
          - brightness: The brightness value greater than 0.0 makes the image brighter in a constant manner while less than 0.0 makes the image darker. default is 0.0.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def gaussian(self, size: int, unsharp: bool = False, mul: float = -1, add: float = 0.0, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Convolves the image by a smoothing guassian kernel.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - unsharp: If true, this method will perform an unsharp mask operation instead of gaussian filtering operation, this improves the clarity of image edges. default is false.
          - mul: This parameter is used to multiply the convolved pixel results. default is auto.
          - add: This parameter is the value to be added to each convolution pixel result. default is 0.0.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def get_histogram(self, thresholds: list[list[int]] = [], invert: bool = False, roi: list[int] = [], bins: int = -1, l_bins: int = 100, a_bins: int = 256, b_bins: int = 256, difference: Image = None) -> Histogram:
        """
        Computes the normalized histogram on all color channels and returns a image::Histogram object.
        
        Args:
          - thresholds: You can define multiple thresholds.
        For GRAYSCALE format, you can use {{Lmin, Lmax}, ...} to define one or more thresholds.
        For RGB888 format, you can use {{Lmin, Lmax, Amin, Amax, Bmin, Bmax}, ...} to define one or more thresholds.
        Where the upper case L,A,B represent the L,A,B channels of the LAB image format, and min, max represent the minimum and maximum values of the corresponding channels.
          - invert: If true, the thresholds will be inverted before the operation. default is false.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - bins: The number of bins to use for the histogram.
        In GRAYSCALE format, setting range is [2, 256], default is 100.
        In RGB888 format, setting range is [2, 100], default is 100.
          - l_bins: The number of bins to use for the l channel of the histogram. Only valid in RGB888 format.
        If an invalid value is set, bins will be used instead. The setting range is [2, 100], default is 100.
          - a_bins: The number of bins to use for the a channel of the histogram.
        Only valid in RGB888 format.The setting range is [2, 256],  default is 256.
          - b_bins: The number of bins to use for the b channel of the histogram.
        Only valid in RGB888 format. The setting range is [2, 256], default is 256.
          - difference: difference may be set to an image object to cause this method to operate on the difference image between the current image and the difference image object.
        default is None.
        
        
        Returns: Returns image::Histogram object
        """
    def get_pixel(self, x: int, y: int, rgbtuple: bool = False) -> list[int]:
        """
        Get pixel of image
        
        Args:
          - x: pixel's coordinate x. x must less than image's width
          - y: pixel's coordinate y. y must less than image's height
          - rgbtuple: switch return value method. rgbtuple decides whether to split the return or not. default is false.
        
        
        Returns: pixel value,
        According to image format and rgbtuple, return different value:
        format is FMT_RGB888, rgbtuple is true, return [R, G, B]; rgbtuple is false, return [RGB]
        foramt is FMT_BGR888, rgbtuple is true, return [B, G, R]; rgbtuple is false, return [BGR]
        format is FMT_GRAYSCALE, return [GRAY];
        """
    def get_regression(self, thresholds: list[list[int]] = [], invert: bool = False, roi: list[int] = [], x_stride: int = 2, y_stride: int = 1, area_threshold: int = 10, pixels_threshold: int = 10, robust: bool = False) -> list[Line]:
        """
        Gets the regression of the image.
        
        Args:
          - thresholds: You can define multiple thresholds.
        For GRAYSCALE format, you can use {{Lmin, Lmax}, ...} to define one or more thresholds.
        For RGB888 format, you can use {{Lmin, Lmax, Amin, Amax, Bmin, Bmax}, ...} to define one or more thresholds.
        Where the upper case L,A,B represent the L,A,B channels of the LAB image format, and min, max represent the minimum and maximum values of the corresponding channels.
          - invert: If true, the image will be inverted before the operation. default is false.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - x_stride: The x stride to use for the regression. default is 2.
          - y_stride: The y stride to use for the regression. default is 1.
          - area_threshold: The area threshold to use for the regression. default is 10.
          - pixels_threshold: The pixels threshold to use for the regression. default is 10.
          - robust: If true, the regression will be robust. default is false.
        
        
        Returns: Returns the regression of the image
        """
    def get_statistics(self, thresholds: list[list[int]] = [], invert: bool = False, roi: list[int] = [], bins: int = -1, l_bins: int = -1, a_bins: int = -1, b_bins: int = -1, difference: Image = None) -> Statistics:
        """
        Gets the statistics of the image. TODO: support in the future
        
        Args:
          - thresholds: You can define multiple thresholds.
        For GRAYSCALE format, you can use {{Lmin, Lmax}, ...} to define one or more thresholds.
        For RGB888 format, you can use {{Lmin, Lmax, Amin, Amax, Bmin, Bmax}, ...} to define one or more thresholds.
        Where the upper case L,A,B represent the L,A,B channels of the LAB image format, and min, max represent the minimum and maximum values of the corresponding channels.
          - invert: If true, the image will be inverted before the operation. default is false.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - bins: The number of bins to use for the statistics. default is -1.
          - l_bins: The number of bins to use for the l channel of the statistics. default is -1.
          - a_bins: The number of bins to use for the a channel of the statistics. default is -1.
          - b_bins: The number of bins to use for the b channel of the statistics. default is -1.
          - difference: The difference image to use for the statistics. default is None.
        
        
        Returns: Returns the statistics of the image
        """
    def height(self) -> int:
        """
        Get image's height
        """
    def histeq(self, adaptive: bool = False, clip_limit: int = -1, mask: Image = None) -> Image:
        """
        Runs the histogram equalization algorithm on the image.
        
        Args:
          - adaptive: If true, an adaptive histogram equalization method will be run on the image instead which as generally better results than non-adaptive histogram qualization but a longer run time. default is false.
          - clip_limit: Provides a way to limit the contrast of the adaptive histogram qualization. Use a small value for this, like 10, to produce good histogram equalized contrast limited images. default is -1.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def invert(self) -> Image:
        """
        Inverts the image in place.
        
        Returns: Returns the image after the operation is completed
        """
    def laplacian(self, size: int, sharpen: bool = False, mul: float = -1, add: float = 0.0, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Convolves the image by a edge detecting laplacian kernel.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - sharpen: If True, this method will sharpen the image instead of an unthresholded edge detection image. Then increase the kernel size to improve image clarity. default is false.
          - mul: This parameter is used to multiply the convolved pixel results. default is auto.
          - add: This parameter is the value to be added to each convolution pixel result. default is 0.0.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def lens_corr(self, strength: float = 1.8, zoom: float = 1.0, x_corr: float = 0.0, y_corr: float = 0.0) -> Image:
        """
        Performs a lens correction operation on the image. TODO: support in the future
        
        Args:
          - strength: The strength of the lens correction. default is 1.8.
          - zoom: The zoom of the lens correction. default is 1.0.
          - x_corr: The x correction of the lens correction. default is 0.0.
          - y_corr: The y correction of the lens correction. default is 0.0.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def linpolar(self, reverse: bool = False) -> Image:
        """
        Re-project’s and image from cartessian coordinates to linear polar coordinates.
        
        Args:
          - reverse: If true, the image will be reverse polar transformed. default is false.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def logpolar(self, reverse: bool = False) -> Image:
        """
        Re-project’s and image from cartessian coordinates to log polar coordinates.
        
        Args:
          - reverse: If true, the image will be reverse polar transformed. default is false.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mask_circle(self, x: int = -1, y: int = -1, radius: int = -1) -> Image:
        """
        Zeros a circular part of the image. If no arguments are supplied this method zeros the center of the image.
        
        Args:
          - x: The x coordinate of the center of the circle.
          - y: The y coordinate of the center of the circle.
          - radius: The radius of the circle.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mask_ellipse(self, x: int = -1, y: int = -1, radius_x: int = -1, radius_y: int = -1, rotation_angle_in_degrees: float = 0) -> Image:
        """
        Zeros a ellipse part of the image. If no arguments are supplied this method zeros the center of the image.
        
        Args:
          - x: The x coordinate of the center of the ellipse.
          - y: The y coordinate of the center of the ellipse.
          - radius_x: The radius of the ellipse in the x direction.
          - radius_y: The radius of the ellipse in the y direction.
          - rotation_angle_in_degrees: The rotation angle of the ellipse in degrees.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mask_rectange(self, x: int = -1, y: int = -1, w: int = -1, h: int = -1) -> Image:
        """
        Zeros a rectangular part of the image. If no arguments are supplied this method zeros the center of the image.
        
        Args:
          - x: The x coordinate of the top left corner of the rectangle.
          - y: The y coordinate of the top left corner of the rectangle.
          - w: The width of the rectangle.
          - h: The height of the rectangle.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def match_lbp_descriptor(self, desc1: LBPKeyPoint, desc2: LBPKeyPoint) -> int:
        """
        Matches the lbp descriptor of the image.  TODO: support in the future
        
        Args:
          - desc1: The descriptor to use for the match.
          - desc2: The descriptor to use for the match.
        
        
        Returns: Returns the match of the image
        """
    def match_orb_descriptor(self, desc1: ORBKeyPoint, desc2: ORBKeyPoint, threshold: int = 95, filter_outliers: bool = False) -> KPTMatch:
        """
        Matches the orb descriptor of the image. TODO: support in the future
        
        Args:
          - desc1: The descriptor to use for the match.
          - desc2: The descriptor to use for the match.
          - threshold: The threshold to use for the match. default is 95.
          - filter_outliers: If true, the image will be filter_outliers before the operation. default is false.
        
        
        Returns: Returns the match of the image
        """
    def max(self, other: Image, mask: Image = None) -> Image:
        """
        Caculate the maximum of each pixel in the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mean(self, size: int, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Standard mean blurring filter using a box filter.
        The parameters offset and invert are valid when threshold is True.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mean_pool(self, x_div: int, y_div: int, copy: bool = False) -> Image:
        """
        Finds the mean of x_div * y_div squares in the image and returns the modified image composed of the mean of each square.
        
        Args:
          - x_div: The width of the squares.
          - y_div: The height of the squares.
          - copy: Select whether to return a new image or modify the original image. default is false.
        If true, returns a new image composed of the mean of each square; If false, returns the modified image composed of the mean of each square.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def median(self, size: int, percentile: float = 0.5, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Runs the median filter on the image. The median filter is the best filter for smoothing surfaces while preserving edges but it is very slow.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - percentile: This parameter controls the percentile of the value used in the kernel. You can set this to 0 for a min filter, 0.25 for a lower quartile filter, 0.75 for an upper quartile filter, and 1.0 for a max filter. default is 0.5.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def midpoint(self, size: int, bias: float = 0.5, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Runs the midpoint filter on the image.This filter finds the midpoint (max * bias + min * (1 - bias)) of each pixel neighborhood in the image.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - bias: The bias of the midpoint. default is 0.5.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def midpoint_pool(self, x_div: int, y_div: int, bias: float = 0.5, copy: bool = False) -> Image:
        """
        Finds the midpoint of x_div * y_div squares in the image and returns the modified image composed of the mean of each square.
        
        Args:
          - x_div: The width of the squares.
          - y_div: The height of the squares.
          - bias: The bias of the midpoint. default is 0.5.
        midpoint value is equal to (max * bias + min * (1 - bias))
          - copy: Select whether to return a new image or modify the original image. default is false.
        If true, returns a new image composed of the midpoint of each square; If false, returns the modified image composed of the midpoint of each square.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def min(self, other: Image, mask: Image = None) -> Image:
        """
        Caculate the minimum of each pixel in the image and the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mode(self, size: int, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Runs the mode filter on the image by replacing each pixel with the mode of their neighbors.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def morph(self, size: int, kernel: list[int], mul: float = -1, add: float = 0.0, threshold: bool = False, offset: int = 0, invert: bool = False, mask: Image = None) -> Image:
        """
        Convolves the image by a filter kernel. This allows you to do general purpose convolutions on an image.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - kernel: The kernel used for convolution. The kernel should be a list of lists of numbers. The kernel should be the same size as the actual kernel size.
          - mul: This parameter is used to multiply the convolved pixel results. default is auto.
          - add: This parameter is the value to be added to each convolution pixel result. default is 0.0.
          - threshold: If true, which will enable adaptive thresholding of the image which sets pixels to white or black based on a pixel’s brightness in relation to the brightness of the kernel of pixels around them.
        default is false.
          - offset: The larger the offset value, the lower brightness pixels on the original image will be set to white. default is 0.
          - invert: If true, the image will be inverted before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def mul(self, other: Image, invert: bool = False, mask: Image = None) -> Image:
        """
        Multiplies the image by the other image.
        Note: This method is meant for image blending and cannot multiply the pixels in the image by a scalar like 2.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.    TODO: support path?
          - invert: If true, the image will be change the multiplication operation from a*b to 1/((1/a)*(1/b)).
        In particular, this lightens the image instead of darkening it (e.g. multiply versus burn operations). default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def negate(self) -> Image:
        """
        Flips (numerically inverts) all pixels values in an image
        
        Returns: Returns the image after the operation is completed.
        """
    def open(self, size: int, threshold: int = 0, mask: Image = None) -> Image:
        """
        Performs erosion and dilation on an image in order.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: As the threshold for erosion and dilation, the actual threshold for erosion is (kernel_size - 1 - threshold), the actual threshold for dialation is threshold. default is 0.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def perspective(self, src_points: list[int], dst_points: list[int], width: int = -1, height: int = -1, method: ResizeMethod = ...) -> Image:
        """
        Perspective transform image, will create a new transformed image object, need 4 points.
        
        Args:
          - src_points: three source points, [x1, y1, x2, y2, x3, y3, x4, y4]
          - dst_points: three destination points, [x1, y1, x2, y2, x3, y3, x4, y4]
          - width: new width, if value is -1, will use height to calculate aspect ratio
          - height: new height, if value is -1, will use width to calculate aspect ratio
          - method: resize method, by default is bilinear
        
        
        Returns: new transformed image object
        """
    def replace(self, other: Image = None, hmirror: bool = False, vflip: bool = False, transpose: bool = False, mask: Image = None) -> Image:
        """
        Replaces all pixels in the image with the corresponding pixels in the other image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - hmirror: If true, the image will be horizontally mirrored before the operation. default is false.
          - vflip: If true, the image will be vertically flipped before the operation. default is false.
          - transpose: If true, the image can be used to rotate 90 degrees or 270 degrees.
        hmirror = false, vflip = false, transpose = false, the image will not be rotated.
        hmirror = false, vflip = true, transpose = true, the image will be rotated 90 degrees.
        hmirror = true, vflip = true, transpose = false, the image will be rotated 180 degrees.
        hmirror = true, vflip = false, transpose = true, the image will be rotated 270 degrees.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def resize(self, width: int, height: int, fit: Fit = ..., method: ResizeMethod = ...) -> Image:
        """
        Resize image, will create a new resized image object
        
        Args:
          - width: new width, if value is -1, will use height to calculate aspect ratio
          - height: new height, if value is -1, will use width to calculate aspect ratio
          - fit: fill, contain, cover, by default is fill
          - method: resize method, by default is NEAREST
        
        
        Returns: Always return a new resized image object even size not change, So in C++ you should take care of the return value to avoid memory leak.
        And it's better to judge whether the size has changed before calling this function to make the program more efficient.
        e.g.
        if img->width() != width || img->height() != height:
        img = img->resize(width, height);
        """
    def resize_map_pos(self, w_out: int, h_out: int, fit: Fit, x: int, y: int, w: int = -1, h: int = -1) -> list[int]:
        """
        map point position or rectangle position from this image size to another image size(resize)
        
        Args:
          - int: h_out target image height
          - fit: resize method, see maix.image.Fit
          - x: original point x, or rectagle left-top point's x
          - y: original point y, or rectagle left-top point's y
          - w: original rectagle width, can be -1 if not use this arg, default -1.
          - h: original rectagle height, can be -1 if not use this arg, default -1.
        
        
        Returns: list type, [x, y] if map point, [x, y, w, h] if resize rectangle.
        """
    def rotate(self, angle: float, width: int = -1, height: int = -1, method: ResizeMethod = ...) -> Image:
        """
        Rotate image, will create a new rotated image object
        
        Args:
          - angle: anti-clock wise rotate angle, if angle is 90 or 270, and width or height is -1, will swap width and height, or will throw exception
          - width: new width, if value is -1, will use height to calculate aspect ratio
          - height: new height, if value is -1, will use width to calculate aspect ratio
          - method: resize method, by default is bilinear
        
        
        Returns: new rotated image object
        """
    def rotation_corr(self, x_rotation: float = 0.0, y_rotation: float = 0.0, z_rotation: float = 0.0, x_translation: float = 0.0, y_translation: float = 0.0, zoom: float = 1.0, fov: float = 60.0, corners: list[float] = []) -> Image:
        """
        Performs a rotation correction operation on the image. TODO: support in the future
        
        Args:
          - x_rotation: The x rotation of the rotation correction. default is 0.0.
          - y_rotation: The y rotation of the rotation correction. default is 0.0.
          - z_rotation: The z rotation of the rotation correction. default is 0.0.
          - x_translation: The x translation of the rotation correction. default is 0.0.
          - y_translation: The y translation of the rotation correction. default is 0.0.
          - zoom: The zoom of the rotation correction. default is 1.0.
          - fov: The fov of the rotation correction. default is 60.0.
          - corners: The corners of the rotation correction. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def save(self, path: str, quality: int = 95) -> maix._maix.err.Err:
        """
        Save image to file
        
        Args:
          - path: file path
          - quality: image quality, by default(value is 95), support jpeg and png format
        
        
        Returns: error code, err::ERR_NONE is ok, other is error
        """
    def search_line_path(self, threshold: int = 30, merge_degree: int = 10, min_len_of_new_path: int = 10) -> list[LineGroup]:
        """
        Search the path of line
        
        Args:
          - threshold: Threshold for finding a line, the larger the value the more accurate the line is found
          - merge_degree: Minimum angle difference required when merging multiple lines
          - min_len_of_new_path: The minimum length of a new path, if the crossing length exceeds this value, it is considered a new path.
        
        
        Returns: Return the line when found lines, format is (groupline1, groupline2, ...), you can use LineGroup class methods to do more operations
        """
    def set(self, other: Image, hmirror: bool = False, vflip: bool = False, transpose: bool = False, mask: Image = None) -> Image:
        """
        Alias for Image::replace.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.
          - hmirror: If true, the image will be horizontally mirrored before the operation. default is false.
          - vflip: If true, the image will be vertically flipped before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def set_pixel(self, x: int, y: int, pixel: list[int]) -> maix._maix.err.Err:
        """
        Set pixel of image
        
        Args:
          - x: pixel's coordinate x. x must less than image's width
          - y: pixel's coordinate y. y must less than image's height
          - pixel: pixel value, according to image format and size of pixel, has different operation:
        format is FMT_RGB888, pixel size must be 1 or 3, if size is 1, will split pixel[0] to [R, G, B]; if size is 3, will use pixel directly
        format is FMT_BGR888, pixel size must be 1 or 3, if size is 1, will split pixel[0] to [B, G, R]; if size is 3, will use pixel directly
        format is FMT_GRAYSCALE, pixel size must be 1, will use pixel directly
        
        
        Returns: error code, Err::ERR_NONE is ok, other is error
        """
    def size(self) -> Size:
        """
        Get image's size, [width, height]
        """
    def sub(self, other: Image, reverse: bool = False, mask: Image = None) -> Image:
        """
        Subtracts the other image from the image.
        
        Args:
          - other: The other image should be an image and should be the same size as the image being operated on.    TODO: support path?
          - reverse: If true, the image will be reversed before the operation. default is false.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def to_format(self, format: Format) -> Image:
        """
        Convert image to specific format
        
        Args:
          - format: format want to convert to, @see image::Format, only support RGB888, BGR888, RGBA8888, BGRA8888, GRAYSCALE, JPEG.
        
        
        Returns: new image object. Need be delete by caller in C++.
        """
    def to_jpeg(self, quality: int = 95, buff: capsule = None, buff_size: int = 0) -> Image:
        """
        Convert image to jpeg
        
        Args:
          - quality: the quality of jpg, default is 95. For MaixCAM supported range is (50, 100], if <= 50 will be fixed to 51.
          - buff: user's buffer, if buff is nullptr, will malloc memory for new image data, else will use buff directly
          - buff_size: the size of buff, if buff is nullptr, buff_size is ignored.
        
        
        Returns: new image object. Need be delete by caller in C++.
        """
    def to_str(self) -> str:
        """
        To string method
        """
    def to_tensor(self, chw: bool = False, copy: bool = True) -> maix._maix.tensor.Tensor:
        """
        Convert Image object to tensor::Tensor object
        
        Args:
          - chw: convert to tensor with CHW or HWC layout result, image is HWC,
        so default chw is false, if set true, will convert to CHW layout.
        Attention, if set chw to true, copy must be true, or will raise err.Exception.
          - copy: if true, will alloc memory for tensor data, else will use the memory of Image object.
        Attention, if set chw to true, copy must be true, or will raise err.Exception.
        
        
        Returns: tensor::Tensor object pointer, an allocated tensor object
        """
    def to_tensor_float32(self, chw: bool = False, mean: list[float] = [], scale: list[float] = []) -> maix._maix.tensor.Tensor:
        """
        Convert image to float32 tensor, and support normlize with mean and scale(1/std).
        If mean and scale not empty, Will execute (data - mean) * scale, and return float32 tensor.Tensor.
        
        Args:
          - chw: convert to chw layout or not, default false.
          - mean: mean value, list type, can be on or three elements according to image's format. Default empty means not normalize.
          - scale: scale value, list type, can be on or three elements according to image's format.  Default empty means not normalize.
        
        
        Returns: float32 tensor.Tensor object with new alloc memory, so you need to delete it manually in C++.
        """
    def top_hat(self, size: int, threshold: int = 0, mask: Image = None) -> Image:
        """
        Returns the image difference of the image and Image.open()’ed image.
        
        Args:
          - size: Kernel size. The actual kernel size is ((size * 2) + 1) * ((size * 2) + 1). Use 1(3x3 kernel), 2(5x5 kernel).
          - threshold: As the threshold for open method. default is 0.
          - mask: Mask is another image to use as a pixel level mask for the operation. The mask should be an image with just black or white pixels and should be the same size as the image being operated on.
        Only pixels set in the mask are modified. default is None.
        
        
        Returns: Returns the image after the operation is completed.
        """
    def width(self) -> int:
        """
        Get image's width
        """
class KPTMatch:
    def __init__(self, cx: int, cy: int, x: int, y: int, w: int, h: int, score: int, theta: int, match: int) -> None:
        ...
class KeyPoint:
    def __init__(self, x: int, y: int, score: int, octave: int, angle: int, matched: int, desc: list[int]) -> None:
        ...
class LBPKeyPoint:
    def __init__(self, data: list[int]) -> None:
        ...
class Line:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] get x1 of line
        [1] get y1 of line
        [2] get x2 of line
        [3] get y2 of line
        [4] get length of line
        [5] get magnitude of the straight line after Hough transformation
        [6] get angle of the straight line after Hough transformation (0-179 degrees)
        [7] get p-value of the straight line after Hough transformation
        
        
        Returns: int&
        """
    def __init__(self, x1: int, y1: int, x2: int, y2: int, magnitude: int = 0, theta: int = 0, rho: int = 0) -> None:
        ...
    def length(self) -> int:
        """
        get length of line
        
        Returns: return length of the line, type is int
        """
    def magnitude(self) -> int:
        """
        get magnitude of the straight line after Hough transformation
        
        Returns: return magnitude, type is int
        """
    def rho(self) -> int:
        """
        get p-value of the straight line after Hough transformation
        
        Returns: return p-value, type is int
        """
    def theta(self) -> int:
        """
        get angle of the straight line after Hough transformation (0-179 degrees)
        
        Returns: return angle, type is int
        """
    def x1(self) -> int:
        """
        get x1 of line
        
        Returns: return x1 of the line, type is int
        """
    def x2(self) -> int:
        """
        get x2 of line
        
        Returns: return x2 of the line, type is int
        """
    def y1(self) -> int:
        """
        get y1 of line
        
        Returns: return y1 of the line, type is int
        """
    def y2(self) -> int:
        """
        get y2 of line
        
        Returns: return y2 of the line, type is int
        """
class LineGroup:
    def __init__(self, id: int, type: LineType, lines: list[Line]) -> None:
        ...
    def id(self) -> int:
        """
        Get the line id of group, first id is 0.
        
        Returns: return id
        """
    def lines(self) -> list[Line]:
        """
        Get a list of line
        
        Returns: returns a list composed of Line objects
        """
    def type(self) -> LineType:
        """
        Get the line type of group
        
        Returns: returns line type. @see LineType
        """
class LineType:
    """
    Members:
    
      LINE_NORMAL
    
      LINE_CROSS
    
      LINE_T
    
      LINE_L
    """
    LINE_CROSS: typing.ClassVar[LineType]  # value = <LineType.LINE_CROSS: 1>
    LINE_L: typing.ClassVar[LineType]  # value = <LineType.LINE_L: 3>
    LINE_NORMAL: typing.ClassVar[LineType]  # value = <LineType.LINE_NORMAL: 0>
    LINE_T: typing.ClassVar[LineType]  # value = <LineType.LINE_T: 2>
    __members__: typing.ClassVar[dict[str, LineType]]  # value = {'LINE_NORMAL': <LineType.LINE_NORMAL: 0>, 'LINE_CROSS': <LineType.LINE_CROSS: 1>, 'LINE_T': <LineType.LINE_T: 2>, 'LINE_L': <LineType.LINE_L: 3>}
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
class ORBKeyPoint:
    def __init__(self, data: list[KeyPoint], threshold: int, normalized: bool) -> None:
        ...
    def get_data(self) -> list[KeyPoint]:
        """
        get data of ORBKeyPoint
        
        Returns: return data of the ORBKeyPoint, type is std::vector<KeyPoint>
        """
class Percentile:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        """
    def __init__(self, l_value: int, a_value: int = 0, b_value: int = 0) -> None:
        ...
    def a_value(self) -> int:
        """
        Return the a channel percentile value of lab format (between -128 and 127).
        
        Returns: returns a channel percentile value
        """
    def b_value(self) -> int:
        """
        Return the b channel percentile value of lab format (between -128 and 127).
        
        Returns: returns b channel percentile value
        """
    def l_value(self) -> int:
        """
        Return the l channel percentile value of lab format (between 0 and 100).
        
        Returns: returns l channel percentile value
        """
    def value(self) -> int:
        """
        Return the grayscale percentile value (between 0 and 255).
        
        Returns: returns grayscale percentile value
        """
class QRCode:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] Returns the qrcode’s bounding box x coordinate
        [1] Returns the qrcode’s bounding box y coordinate
        [2] Returns the qrcode’s bounding box w coordinate
        [3] Returns the qrcode’s bounding box h coordinate
        [4] Not support this index, try to use payload() method
        [5] Returns the version of qrcode
        [6] Returns the error correction level of qrcode
        [7] Returns the mask of qrcode
        [8] Returns the datatype of qrcode
        [9] Returns the eci of qrcode
        
        
        Returns: int&
        """
    def __init__(self, rect: list[int], corners: list[list[int]], payload: str, version: int, ecc_level: int, mask: int, data_type: int, eci: int) -> None:
        ...
    def corners(self) -> list[list[int]]:
        """
        get coordinate of QRCode
        
        Returns: return the coordinate of the QRCode.
        """
    def data_type(self) -> int:
        """
        get QRCode dataType
        
        Returns: return mask of the QRCode
        """
    def ecc_level(self) -> int:
        """
        get QRCode error correction level
        
        Returns: return error correction level of the QRCode
        """
    def eci(self) -> int:
        """
        get QRCode eci
        
        Returns: return data of the QRCode
        """
    def h(self) -> int:
        """
        get h of QRCode
        
        Returns: return h of the QRCode, type is int
        """
    def is_alphanumeric(self) -> bool:
        """
        check QRCode is alphanumeric
        
        Returns: return true if the result type of the QRCode is alphanumeric
        """
    def is_binary(self) -> bool:
        """
        check QRCode is binary
        
        Returns: return true if the result type of the QRCode is binary
        """
    def is_kanji(self) -> bool:
        """
        check QRCode is kanji
        
        Returns: return true if the result type of the QRCode is kanji
        """
    def is_numeric(self) -> bool:
        """
        check QRCode is numeric
        
        Returns: return true if the result type of the QRCode is numeric
        """
    def mask(self) -> int:
        """
        get QRCode mask
        
        Returns: return mask of the QRCode
        """
    def payload(self) -> str:
        """
        get QRCode payload
        
        Returns: return area of the QRCode
        """
    def rect(self) -> list[int]:
        """
        get rectangle of QRCode
        
        Returns: return the rectangle of the QRCode. format is {x, y, w, h}, type is std::vector<int>
        """
    def version(self) -> int:
        """
        get QRCode version
        
        Returns: return version of the QRCode
        """
    def w(self) -> int:
        """
        get w of QRCode
        
        Returns: return w of the QRCode, type is int
        """
    def x(self) -> int:
        """
        get x of QRCode
        
        Returns: return x of the QRCode, type is int
        """
    def y(self) -> int:
        """
        get y of QRCode
        
        Returns: return y of the QRCode, type is int
        """
class QRCodeDecoderType:
    """
    Members:
    
      QRCODE_DECODER_TYPE_ZBAR
    
      QRCODE_DECODER_TYPE_QUIRC
    
      QRCODE_DECODER_TYPE_ZXING
    """
    QRCODE_DECODER_TYPE_QUIRC: typing.ClassVar[QRCodeDecoderType]  # value = <QRCodeDecoderType.QRCODE_DECODER_TYPE_QUIRC: 1>
    QRCODE_DECODER_TYPE_ZBAR: typing.ClassVar[QRCodeDecoderType]  # value = <QRCodeDecoderType.QRCODE_DECODER_TYPE_ZBAR: 0>
    QRCODE_DECODER_TYPE_ZXING: typing.ClassVar[QRCodeDecoderType]  # value = <QRCodeDecoderType.QRCODE_DECODER_TYPE_ZXING: 2>
    __members__: typing.ClassVar[dict[str, QRCodeDecoderType]]  # value = {'QRCODE_DECODER_TYPE_ZBAR': <QRCodeDecoderType.QRCODE_DECODER_TYPE_ZBAR: 0>, 'QRCODE_DECODER_TYPE_QUIRC': <QRCodeDecoderType.QRCODE_DECODER_TYPE_QUIRC: 1>, 'QRCODE_DECODER_TYPE_ZXING': <QRCodeDecoderType.QRCODE_DECODER_TYPE_ZXING: 2>}
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
class QRCodeDetector:
    def __init__(self) -> None:
        ...
    def detect(self, img: Image, roi: list[int] = [], decoder_type: QRCodeDecoderType = ...) -> list[QRCode]:
        """
        Finds all qrcodes in the image.
        
        Args:
          - img: The image to find qrcodes.
          - roi: The region of interest, input in the format of (x, y, w, h), x and y are the coordinates of the upper left corner, w and h are the width and height of roi.
        default is None, means whole image.
          - decoder_type: Select the QR code decoding method. Choosing QRCODE_DECODER_TYPE_QUIRC allows for retrieving QR code version, ECC level, mask, data type, and other details,
        though it may decode slower at lower resolutions. Opting for QRCODE_DECODER_TYPE_ZBAR enables faster decoding at lower resolutions but may slow down at higher resolutions,
        providing only the QR code content and position information. default is QRCODE_DECODER_TYPE_ZBAR.
        
        
        Returns: Returns the qrcodes of the image
        """
class Rect:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: [0] get x of rect
        [1] get y of rect
        [2] get w of rect
        [3] get h of rect
        [4] get magnitude of the straight line after Hough transformation
        
        
        Returns: int&
        """
    def __init__(self, corners: list[list[int]], x: int, y: int, w: int, h: int, magnitude: int = 0) -> None:
        ...
    def corners(self) -> list[list[int]]:
        """
        get corners of rect
        
        Returns: return the coordinate of the rect.
        """
    def h(self) -> int:
        """
        get h of rect
        
        Returns: return h of the rect, type is int
        """
    def magnitude(self) -> int:
        """
        get the rectangle’s magnitude.
        
        Returns: return magnitude, type is int
        """
    def rect(self) -> list[int]:
        """
        get rectangle of rect
        
        Returns: return the rectangle of the rect. format is {x, y, w, h}, type is std::vector<int>
        """
    def w(self) -> int:
        """
        get w of rect
        
        Returns: return w of the rect, type is int
        """
    def x(self) -> int:
        """
        get x of rect
        
        Returns: return x of the rect, type is int
        """
    def y(self) -> int:
        """
        get y of rect
        
        Returns: return y of the rect, type is int
        """
class ResizeMethod:
    """
    Members:
    
      NEAREST
    
      BILINEAR
    
      BICUBIC
    
      AREA
    
      LANCZOS
    
      HAMMING
    
      RESIZE_METHOD_MAX
    """
    AREA: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.AREA: 3>
    BICUBIC: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.BICUBIC: 2>
    BILINEAR: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.BILINEAR: 1>
    HAMMING: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.HAMMING: 5>
    LANCZOS: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.LANCZOS: 4>
    NEAREST: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.NEAREST: 0>
    RESIZE_METHOD_MAX: typing.ClassVar[ResizeMethod]  # value = <ResizeMethod.RESIZE_METHOD_MAX: 6>
    __members__: typing.ClassVar[dict[str, ResizeMethod]]  # value = {'NEAREST': <ResizeMethod.NEAREST: 0>, 'BILINEAR': <ResizeMethod.BILINEAR: 1>, 'BICUBIC': <ResizeMethod.BICUBIC: 2>, 'AREA': <ResizeMethod.AREA: 3>, 'LANCZOS': <ResizeMethod.LANCZOS: 4>, 'HAMMING': <ResizeMethod.HAMMING: 5>, 'RESIZE_METHOD_MAX': <ResizeMethod.RESIZE_METHOD_MAX: 6>}
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
class Size:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: 0 for width, 1 for height
        
        
        Returns: int& width or height
        """
    def __init__(self, width: int = 0, height: int = 0) -> None:
        ...
    def __str__(self) -> str:
        """
        to string
        """
    def height(self, height: int = -1) -> int:
        """
        height of size
        
        Args:
          - height: set new height, if not set, only return current height
        """
    def width(self, width: int = -1) -> int:
        """
        width of size
        
        Args:
          - width: set new width, if not set, only return current width
        """
class Statistics:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        
        Args:
          - index: array index
        
        
        Returns: int&
        """
    def __init__(self, format: Format, l_statistics: list[int], a_statistics: list[int], b_statistics: list[int]) -> None:
        ...
    def a_lq(self) -> int:
        """
        get A channel lq
        
        Returns: return A channel lq, type is int
        """
    def a_max(self) -> int:
        """
        get A channel max
        
        Returns: return A channel max, type is int
        """
    def a_mean(self) -> int:
        """
        get A channel mean
        
        Returns: return A channel mean, type is int
        """
    def a_median(self) -> int:
        """
        get A channea median
        
        Returns: return A channel median, type is int
        """
    def a_min(self) -> int:
        """
        get A channel min
        
        Returns: return A channel min, type is int
        """
    def a_mode(self) -> int:
        """
        get A channel mode
        
        Returns: return A channel mode, type is int
        """
    def a_std_dev(self) -> int:
        """
        get A channel std_dev
        
        Returns: return A channel std_dev, type is int
        """
    def a_uq(self) -> int:
        """
        get A channel uq
        
        Returns: return A channel uq, type is int
        """
    def b_lq(self) -> int:
        """
        get B channel lq
        
        Returns: return B channel lq, type is int
        """
    def b_max(self) -> int:
        """
        get B channel max
        
        Returns: return B channel max, type is int
        """
    def b_mean(self) -> int:
        """
        get B channel mean
        
        Returns: return B channel mean, type is int
        """
    def b_median(self) -> int:
        """
        get B channea median
        
        Returns: return B channel median, type is int
        """
    def b_min(self) -> int:
        """
        get B channel min
        
        Returns: return B channel min, type is int
        """
    def b_mode(self) -> int:
        """
        get B channel mode
        
        Returns: return B channel mode, type is int
        """
    def b_std_dev(self) -> int:
        """
        get B channel std_dev
        
        Returns: return B channel std_dev, type is int
        """
    def b_uq(self) -> int:
        """
        get B channel uq
        
        Returns: return B channel uq, type is int
        """
    def format(self) -> Format:
        """
        get format of Statistics source image
        
        Returns: return format of the Statistics source image, type is image::Format
        """
    def l_lq(self) -> int:
        """
        get L channel lq
        
        Returns: return L channel lq, type is int
        """
    def l_max(self) -> int:
        """
        get L channel max
        
        Returns: return L channel max, type is int
        """
    def l_mean(self) -> int:
        """
        get L channel mean
        
        Returns: return L channel mean, type is int
        """
    def l_median(self) -> int:
        """
        get L channel median
        
        Returns: return L channel median, type is int
        """
    def l_min(self) -> int:
        """
        get L channel min
        
        Returns: return L channel min, type is int
        """
    def l_mode(self) -> int:
        """
        get L channel mode
        
        Returns: return L channel mode, type is int
        """
    def l_std_dev(self) -> int:
        """
        get L channel std_dev
        
        Returns: return L channel std_dev, type is int
        """
    def l_uq(self) -> int:
        """
        get L channel uq
        
        Returns: return L channel uq, type is int
        """
class TemplateMatch:
    """
    Members:
    
      SEARCH_EX
    
      SEARCH_DS
    """
    SEARCH_DS: typing.ClassVar[TemplateMatch]  # value = <TemplateMatch.SEARCH_DS: 1>
    SEARCH_EX: typing.ClassVar[TemplateMatch]  # value = <TemplateMatch.SEARCH_EX: 0>
    __members__: typing.ClassVar[dict[str, TemplateMatch]]  # value = {'SEARCH_EX': <TemplateMatch.SEARCH_EX: 0>, 'SEARCH_DS': <TemplateMatch.SEARCH_DS: 1>}
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
class Threshold:
    def __getitem__(self, index: int) -> int:
        """
        Subscript operator
        """
    def __init__(self, l_value: int, a_value: int = 0, b_value: int = 0) -> None:
        ...
    def a_value(self) -> int:
        """
        Return the a channel threshold value of lab format (between -128 and 127).
        
        Returns: returns a channel percentile value
        """
    def b_value(self) -> int:
        """
        Return the b channel threshold value of lab format (between -128 and 127).
        
        Returns: returns b channel percentile value
        """
    def l_value(self) -> int:
        """
        Return the l channel threshold value of lab format (between 0 and 100).
        
        Returns: returns l channel percentile value
        """
    def value(self) -> int:
        """
        Return the grayscale threshold value (between 0 and 255).
        
        Returns: returns grayscale threshold value
        """
def cmap_color(gray: int, cmap: CMap) -> Color:
    """
    Get the mapped color of a grayscale value under a specific colormap.
    
    Args:
      - gray: Grayscale value in [0, 255].
      - cmap: Colormap enum value to map the grayscale to color.
    
    
    Returns: The mapped image::Color.
    """
def cmap_colors(cmap: CMap) -> list[Color]:
    """
    Get all 256 mapped colors of a colormap.
    
    Args:
      - cmap: Colormap enum value.
    
    
    Returns: Vector of 256 image::Color values corresponding to grayscale values [0, 255].
    Return value will alloc data, you need to delete it after use in C++.
    """
def cmap_colors_rgb(cmap: CMap) -> list[typing_extensions.Annotated[list[int], pybind11_stubgen.typing_ext.FixedSize(3)]]:
    """
    Get all 256 mapped RGB colors of a colormap.
    
    Args:
      - cmap: Colormap enum value.
    
    
    Returns: Vector of 256 RGB arrays (each array has 3 uint8_t: R, G, B).
    Return value is a internal table refrence.
    """
def cmap_from_str(name: str) -> CMap:
    """
    Get the colormap enum value from a string name.
    
    Args:
      - name: Name of the colormap (case-insensitive).
    
    
    Returns: Corresponding colormap enum value, or throws if name is invalid.
    """
def cmap_strs(classify: bool = False) -> list[str]:
    """
    Get a list of all available colormap name strings.
    
    Args:
      - claasify: cmaps for classify, wihch cmap size not equal to 256.
    
    
    Returns: Vector of all supported colormap name strings.
    """
def cmap_to_str(cmap: CMap) -> str:
    """
    Get the string representation of a colormap enum value.
    
    Args:
      - cmap: Colormap enum value, @see image::CMap
    
    
    Returns: Corresponding colormap name as a string.
    """
def cv2image(array: numpy.ndarray[numpy.uint8], bgr: bool = True, copy: bool = True) -> Image:
    """
    OpenCV Mat(numpy array object) to Image object
    
    Args:
      - array: numpy array object, must be a 3-dim or 2-dim continuous array with shape hwc or hw
      - bgr: if set bgr, the return image will be marked as BGR888 or BGRA8888 format(only mark, not ensure return image is real BGR format), grayscale will ignore this arg.
      - copy: if true, will alloc new buffer and copy data, else will directly use array's data buffer, default true.
    Use this arg carefully, when set to false, ther array MUST keep alive until we don't use the return img of this func, or will cause program crash.
    
    
    Returns: Image object
    """
def fonts() -> list[str]:
    """
    Get all loaded fonts
    
    Returns: all loaded fonts, string list type
    """
def format_name(fmt: Format) -> str:
    """
    Get format name by format.
    
    Returns: format name string
    """
def from_bytes(width: int, height: int, format: Format, data: maix.Bytes(bytes), copy: bool = True) -> Image:
    """
    Create image from bytes
    
    Args:
      - width: image width
      - height: image height
      - format: image format
      - data: image data, if data is None, will malloc memory for image data
    If the image is in jpeg format, data must be filled in.
      - copy: if true and data is not None, will copy data to new buffer, else will use data directly. default is true to avoid memory leak.
    Use it carefully!!!
    
    
    Returns: Image object
    """
def image2cv(img: Image, ensure_bgr: bool = True, copy: bool = True) -> numpy.ndarray[numpy.uint8]:
    """
    Image object to OpenCV Mat(numpy array object)
    
    Args:
      - img: Image object, maix.image.Image type.
      - ensure_bgr: auto convert to BGR888 or BGRA8888 if img format is not BGR or BGRA, if set to false, will not auto convert and directly use img's data, default true.
    If copy is false, ensure_bgr always be false.
      - copy: Whether alloc new image and copy data or not, if ensure_bgr and img is not bgr or bgra format, always copy,
    if not copy, array object will directly use img's data buffer, will faster but change array will affect img's data, default true.
    
    
    Returns: numpy array object
    """
def load(path: str, format: Format = ...) -> Image:
    """
    Load image from file, and convert to Image object
    
    Args:
      - path: image file path
      - format: read as this format, if not match, will convert to this format, by default is RGB888
    
    
    Returns: Image object, if load failed, will return None(nullptr in C++), so you should care about it.
    """
def load_font(name: str, path: str, size: int = 16) -> maix._maix.err.Err:
    """
    Load font from file
    
    Args:
      - name: font name, used to identify font
      - path: font file path, support ttf, ttc, otf
      - size: font size, font height, by default is 16
    
    
    Returns: error code, err::ERR_NONE is ok, other is error
    """
def resize_map_pos(w_in: int, h_in: int, w_out: int, h_out: int, fit: Fit, x: int, y: int, w: int = -1, h: int = -1) -> list[int]:
    """
    map point position or rectangle position from one image size to another image size(resize)
    
    Args:
      - int: h_out target image height
      - fit: resize method, see maix.image.Fit
      - x: original point x, or rectagle left-top point's x
      - y: original point y, or rectagle left-top point's y
      - w: original rectagle width, can be -1 if not use this arg, default -1.
      - h: original rectagle height, can be -1 if not use this arg, default -1.
    
    
    Returns: list type, [x, y] if map point, [x, y, w, h] if resize rectangle.
    """
def resize_map_pos_reverse(w_in: int, h_in: int, w_out: int, h_out: int, fit: Fit, x: int, y: int, w: int = -1, h: int = -1) -> list[int]:
    """
    reverse resize_map_pos method, when we call image.resize method resiz image 'a' to image 'b', we want to known the original position on 'a' whith a knew point on 'b'
    
    Args:
      - int: h_out image height after resized
      - fit: resize method, see maix.image.Fit
      - x: point on resized image x, or rectagle left-top point's x
      - y: original point y, or rectagle left-top point's y
      - w: original rectagle width, can be -1 if not use this arg, default -1.
      - h: original rectagle height, can be -1 if not use this arg, default -1.
    
    
    Returns: list type, [x, y] if map point, [x, y, w, h] if resize rectangle.
    """
def set_default_font(name: str) -> maix._maix.err.Err:
    """
    Set default font, if not call this method, default is hershey_plain
    
    Args:
      - name: font name, supported names can be get by fonts()
    
    
    Returns: error code, err::ERR_NONE is ok, other is error
    """
def string_size(string: str, scale: float = 1, thickness: int = 1, font: str = '') -> Size:
    """
    Get text rendered width and height
    
    Args:
      - string: text content
      - scale: font scale, by default(value is 1)
      - thickness: text thickness(line width), by default(value is 1)
    
    
    Returns: text rendered width and height, [width, height]
    """
COLOR_BLACK: Color  # value = <maix._maix.image.Color object>
COLOR_BLUE: Color  # value = <maix._maix.image.Color object>
COLOR_GRAY: Color  # value = <maix._maix.image.Color object>
COLOR_GREEN: Color  # value = <maix._maix.image.Color object>
COLOR_INVALID: Color  # value = <maix._maix.image.Color object>
COLOR_ORANGE: Color  # value = <maix._maix.image.Color object>
COLOR_PURPLE: Color  # value = <maix._maix.image.Color object>
COLOR_RED: Color  # value = <maix._maix.image.Color object>
COLOR_WHITE: Color  # value = <maix._maix.image.Color object>
COLOR_YELLOW: Color  # value = <maix._maix.image.Color object>
fmt_names: list = ['RGB888', 'BGR888', 'RGBA8888', 'BGRA8888', 'RGB565', 'BGR565', 'YUV422SP', 'YUV422P', 'YVU420SP', 'YUV420SP', 'YVU420P', 'YUV420P', 'GRAYSCALE', 'BGGR6', 'GBRG6', 'GRBG6', 'RG6B6', 'BGGR8', 'GBRG8', 'GRBG8', 'RG6B8', 'BGGR10', 'GBRG10', 'GRBG10', 'RG6B10', 'BGGR12', 'GBRG12', 'GRBG12', 'RG6B12', 'UNCOMPRESSED_MAX', 'COMPRESSED_MIN', 'JPEG', 'PNG', 'COMPRESSED_MAX', 'INVALID']
fmt_size: list = [3.0, 3.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 1.5, 1.5, 1.5, 1.5, 1.0, 0.75, 0.75, 0.75, 0.75, 1.0, 1.0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.25, 1.5, 1.5, 1.5, 1.5, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
