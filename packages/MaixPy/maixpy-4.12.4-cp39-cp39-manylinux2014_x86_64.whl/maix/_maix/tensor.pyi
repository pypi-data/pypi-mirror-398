"""
maix.tensor module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['DType', 'Tensor', 'Tensors', 'Vector3f', 'Vector3i16', 'Vector3i32', 'Vector3u16', 'Vector3u32', 'dtype_name', 'dtype_size', 'tensor_from_numpy_float32', 'tensor_from_numpy_int8', 'tensor_from_numpy_uint8', 'tensor_to_numpy_float32', 'tensor_to_numpy_int8', 'tensor_to_numpy_uint8']
class DType:
    """
    Members:
    
      UINT8
    
      INT8
    
      UINT16
    
      INT16
    
      UINT32
    
      INT32
    
      FLOAT16
    
      FLOAT32
    
      FLOAT64
    
      BOOL
    
      DTYPE_MAX
    """
    BOOL: typing.ClassVar[DType]  # value = <DType.BOOL: 9>
    DTYPE_MAX: typing.ClassVar[DType]  # value = <DType.DTYPE_MAX: 10>
    FLOAT16: typing.ClassVar[DType]  # value = <DType.FLOAT16: 6>
    FLOAT32: typing.ClassVar[DType]  # value = <DType.FLOAT32: 7>
    FLOAT64: typing.ClassVar[DType]  # value = <DType.FLOAT64: 8>
    INT16: typing.ClassVar[DType]  # value = <DType.INT16: 3>
    INT32: typing.ClassVar[DType]  # value = <DType.INT32: 5>
    INT8: typing.ClassVar[DType]  # value = <DType.INT8: 1>
    UINT16: typing.ClassVar[DType]  # value = <DType.UINT16: 2>
    UINT32: typing.ClassVar[DType]  # value = <DType.UINT32: 4>
    UINT8: typing.ClassVar[DType]  # value = <DType.UINT8: 0>
    __members__: typing.ClassVar[dict[str, DType]]  # value = {'UINT8': <DType.UINT8: 0>, 'INT8': <DType.INT8: 1>, 'UINT16': <DType.UINT16: 2>, 'INT16': <DType.INT16: 3>, 'UINT32': <DType.UINT32: 4>, 'INT32': <DType.INT32: 5>, 'FLOAT16': <DType.FLOAT16: 6>, 'FLOAT32': <DType.FLOAT32: 7>, 'FLOAT64': <DType.FLOAT64: 8>, 'BOOL': <DType.BOOL: 9>, 'DTYPE_MAX': <DType.DTYPE_MAX: 10>}
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
class Tensor:
    def __init__(self, shape: list[int], dtype: DType) -> None:
        ...
    def __str__(self) -> str:
        """
        To string
        """
    def argmax(self, axis: int = 65535) -> Tensor:
        """
        argmax of tensor
        
        Args:
          - axis: By default, the index is into the flattened array, otherwise along the specified axis., wrong axis will throw an err::Exception
        
        
        Returns: argmax result, you need to delete it after use in C++.
        """
    def argmax1(self) -> int:
        """
        argmax1, flattened data max index
        
        Returns: argmax result, int type
        """
    def dtype(self) -> DType:
        """
        get tensor data type
        
        Returns: tensor data type, see DType of this module
        """
    def expand_dims(self, axis: int) -> None:
        """
        expand tensor shape
        
        Args:
          - axis: axis to expand
        """
    def flatten(self) -> None:
        """
        Flatten tensor shape to 1D
        """
    def reshape(self, shape: list[int]) -> None:
        """
        reshape tensor shape, if size not match, it will throw an err::Exception
        
        Args:
          - shape: new shape
        """
    def shape(self) -> list[int]:
        """
        get tensor shape
        
        Returns: tensor shape, a int list
        """
    def to_float_list(self) -> list[float]:
        """
        get tensor data and return a list
        
        Returns: list type data
        """
    def to_str(self) -> str:
        """
        To string
        """
class Tensors:
    tensors: dict[str, Tensor]
    def __getitem__(self, key: str) -> Tensor:
        """
        Operator []
        """
    def __init__(self) -> None:
        ...
    def __len__(self) -> int:
        """
        Size
        """
    def add_tensor(self, key: str, tensor: Tensor, copy: bool, auto_delete: bool) -> None:
        """
        Add tensor
        """
    def clear(self) -> None:
        """
        Clear tensors
        """
    def get_tensor(self, key: str) -> Tensor:
        """
        Get tensor by key
        """
    def keys(self) -> list[str]:
        """
        Get names
        """
    def rm_tensor(self, key: str) -> None:
        """
        Remove tensor
        """
class Vector3f:
    x: float
    y: float
    z: float
    def __init__(self, x0: float, y0: float, z0: float) -> None:
        ...
class Vector3i16:
    x: int
    y: int
    z: int
    def __init__(self, x0: int, y0: int, z0: int) -> None:
        ...
class Vector3i32:
    x: int
    y: int
    z: int
    def __init__(self, x0: int, y0: int, z0: int) -> None:
        ...
class Vector3u16:
    x: int
    y: int
    z: int
    def __init__(self, x0: int, y0: int, z0: int) -> None:
        ...
class Vector3u32:
    x: int
    y: int
    z: int
    def __init__(self, x0: int, y0: int, z0: int) -> None:
        ...
def tensor_from_numpy_float32(array: numpy.ndarray[numpy.float32], copy: bool = True) -> Tensor:
    """
    float32 type numpy ndarray object to tensor.Tensor object.
    
    Args:
      - array: numpy array object.
      - copy: if true, will alloc new buffer and copy data, else will directly use array's data buffer, default true.
    Use this arg carefully, when set to false, ther array MUST keep alive until we don't use the return tensor of this func, or will cause program crash.
    
    
    Returns: tensor.Tensor object.
    """
def tensor_from_numpy_int8(array: numpy.ndarray[numpy.int8], copy: bool = True) -> Tensor:
    """
    int8 type numpy ndarray object to tensor.Tensor object.
    
    Args:
      - array: numpy array object.
      - copy: if true, will alloc new buffer and copy data, else will directly use array's data buffer, default true.
    Use this arg carefully, when set to false, ther array MUST keep alive until we don't use the return tensor of this func, or will cause program crash.
    
    
    Returns: tensor.Tensor object.
    """
def tensor_from_numpy_uint8(array: numpy.ndarray[numpy.uint8], copy: bool = True) -> Tensor:
    """
    uint8 type numpy ndarray object to tensor.Tensor object.
    
    Args:
      - array: numpy array object.
      - copy: if true, will alloc new buffer and copy data, else will directly use array's data buffer, default true.
    Use this arg carefully, when set to false, ther array MUST keep alive until we don't use the return tensor of this func, or will cause program crash.
    
    
    Returns: tensor.Tensor object.
    """
def tensor_to_numpy_float32(t: Tensor, copy: bool = True) -> numpy.ndarray[numpy.float32]:
    """
    tensor.Tensor object to float32 type numpy ndarray object.
    
    Args:
      - t: tensor.Tensor object.
      - copy: Whether alloc new Tensor and copy data or not,
    if not copy, array object will directly use arg's data buffer, will faster but change array will affect arg's data, default true.
    
    
    Returns: numpy array object
    """
def tensor_to_numpy_int8(t: Tensor, copy: bool = True) -> numpy.ndarray[numpy.int8]:
    """
    tensor.Tensor object to int8 type numpy ndarray object.
    
    Args:
      - t: tensor.Tensor object.
      - copy: Whether alloc new Tensor and copy data or not,
    if not copy, array object will directly use arg's data buffer, will faster but change array will affect arg's data, default true.
    
    
    Returns: numpy array object
    """
def tensor_to_numpy_uint8(t: Tensor, copy: bool = True) -> numpy.ndarray[numpy.uint8]:
    """
    tensor.Tensor object to int8 type numpy ndarray object.
    
    Args:
      - t: tensor.Tensor object.
      - copy: Whether alloc new Tensor and copy data or not,
    if not copy, array object will directly use arg's data buffer, will faster but change array will affect arg's data, default true.
    
    
    Returns: numpy array object
    """
dtype_name: list = ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'float16', 'float32', 'float64', 'bool', 'invalid']
dtype_size: list = [1, 1, 2, 2, 4, 4, 2, 4, 8, 1, 0]
