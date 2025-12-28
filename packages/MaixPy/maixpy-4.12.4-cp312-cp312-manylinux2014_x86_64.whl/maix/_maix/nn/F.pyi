"""
maix.nn.F module
"""
from __future__ import annotations
import maix._maix.tensor
__all__: list[str] = ['softmax']
def softmax(tensor: maix._maix.tensor.Tensor, replace: bool) -> maix._maix.tensor.Tensor:
    """
    Softmax, only support 1D tensor, multi-dimension tensor will be treated as 1D tensor
    
    Args:
      - tensor: input tensor
      - replace: change input tensor data directly, if not, will create a new tensor
    
    
    Returns: output tensor, if arg replace is true, return the arg tensor's address.
    If not replace, return a new object, so In C++, you should delete it manually in this case!
    """
