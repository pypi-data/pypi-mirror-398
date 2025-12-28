"""
example module, this will be maix.example module in MaixPy, maix::example namespace in MaixCDK
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Example', 'Kind', 'Kind2', 'Test', 'change_arg_name', 'change_arg_name2', 'hello', 'list_var', 'test_var', 'var1']
class Example:
    hello_str: typing.ClassVar[str] = 'hello '
    age: int
    name: str
    @staticmethod
    def callback(cb: typing.Callable[[int, int], int]) -> int:
        """
        Callback example
        
        Args:
          - cb: callback function, param is two int type, return is int type
        
        
        Returns: int type, return value is cb's return value.
        """
    @staticmethod
    def callback2(cb: typing.Callable[[list[int], int], int]) -> int:
        """
        Callback example
        
        Args:
          - cb: callback function, param is a int list type and int type, return is int type
        
        
        Returns: int type, return value is cb's return value.
        """
    @staticmethod
    def dict_test() -> dict[str, Test]:
        """
        dict_test, return dict type, and element is pointer type(alloc in C++).
        Here when the returned Tensor object will auto delete by Python GC.
        """
    @staticmethod
    def hello(name: str) -> str:
        """
        say hello to someone
        
        Args:
          - name: name of someone, string type
        
        
        Returns: string type, content is Example::hello_str + name
        """
    @staticmethod
    def hello_bytes(*args, **kwargs):
        """
        param is bytes example
        
        Args:
          - bytes: bytes type param
        
        
        Returns: bytes type, return value is bytes changed value
        """
    @staticmethod
    def hello_dict(dict: dict[str, int]) -> dict[str, int]:
        """
        Dict param example
        
        Args:
          - dict: dict type param, key is string type, value is int type
        """
    def __init__(self, name: str, age: int = 18, pet: Kind = ...) -> None:
        ...
    def get_age(self) -> int:
        """
        get age of Example
        
        Returns: age of Example, int type, value range is [0, 100]
        """
    def get_dict(self, in: dict[str, int]) -> dict[str, int]:
        """
        Example dict API
        
        Args:
          - in: direction [in], input dict, key is string type, value is int type.
        In MaixPy, you can pass `dict` to this API
        
        
        Returns: dict, key is string type, value is int type, content is {"a": 1} + in
        In MaixPy, return type is `dict` object
        """
    def get_list(self, in: list[int]) -> list[int]:
        """
        get list example
        
        Args:
          - in: direction [in], input list, items are int type.
        In MaixPy, you can pass list or tuple to this API
        
        
        Returns: list, items are int type, content is [1, 2, 3] + in. Alloc item, del in MaixPy will auto free memory.
        """
    def get_name(self) -> str:
        """
        get name of Example
        you can also get name by property `name`.
        
        Returns: name of Example, string type
        """
    def get_pet(self) -> Kind:
        """
        Example enum member
        """
    def set_age(self, age: int) -> None:
        """
        set age of Example
        
        Args:
          - age: age of Example, int type, value range is [0, 100]
        """
    def set_name(self, name: str) -> None:
        """
        set name of Example
        
        Args:
          - name: name of Example, string type
        """
    def set_pet(self, pet: Kind) -> None:
        """
        Example enum member
        """
    @property
    def var1(self) -> str:
        ...
    @property
    def var2(self) -> str:
        ...
class Kind:
    """
    Members:
    
      KIND_NONE
    
      KIND_DOG
    
      KIND_CAT
    
      KIND_BIRD
    
      KIND_MAX
    """
    KIND_BIRD: typing.ClassVar[Kind]  # value = <Kind.KIND_BIRD: 3>
    KIND_CAT: typing.ClassVar[Kind]  # value = <Kind.KIND_CAT: 2>
    KIND_DOG: typing.ClassVar[Kind]  # value = <Kind.KIND_DOG: 1>
    KIND_MAX: typing.ClassVar[Kind]  # value = <Kind.KIND_MAX: 4>
    KIND_NONE: typing.ClassVar[Kind]  # value = <Kind.KIND_NONE: 0>
    __members__: typing.ClassVar[dict[str, Kind]]  # value = {'KIND_NONE': <Kind.KIND_NONE: 0>, 'KIND_DOG': <Kind.KIND_DOG: 1>, 'KIND_CAT': <Kind.KIND_CAT: 2>, 'KIND_BIRD': <Kind.KIND_BIRD: 3>, 'KIND_MAX': <Kind.KIND_MAX: 4>}
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
class Kind2:
    """
    Members:
    
      NONE
    
      DOG
    
      CAT
    
      BIRD
    
      MAX
    """
    BIRD: typing.ClassVar[Kind2]  # value = <Kind2.BIRD: 3>
    CAT: typing.ClassVar[Kind2]  # value = <Kind2.CAT: 2>
    DOG: typing.ClassVar[Kind2]  # value = <Kind2.DOG: 1>
    MAX: typing.ClassVar[Kind2]  # value = <Kind2.MAX: 4>
    NONE: typing.ClassVar[Kind2]  # value = <Kind2.NONE: 0>
    __members__: typing.ClassVar[dict[str, Kind2]]  # value = {'NONE': <Kind2.NONE: 0>, 'DOG': <Kind2.DOG: 1>, 'CAT': <Kind2.CAT: 2>, 'BIRD': <Kind2.BIRD: 3>, 'MAX': <Kind2.MAX: 4>}
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
class Test:
    def __init__(self) -> None:
        ...
def change_arg_name(e: Example) -> Example:
    """
    Change arg name example
    
    Args:
      - e: Example object
    
    
    Returns: same as arg
    """
def change_arg_name2(e: Example) -> None:
    """
    Change arg name example
    
    Args:
      - e: Example object
    """
def hello(name: str) -> str:
    """
    say hello to someone
    
    Args:
      - name: direction [in], name of someone, string type
    
    
    Returns: string type, content is hello + name
    """
list_var: list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
test_var: int = 100
var1: str = 'Sipeed'
