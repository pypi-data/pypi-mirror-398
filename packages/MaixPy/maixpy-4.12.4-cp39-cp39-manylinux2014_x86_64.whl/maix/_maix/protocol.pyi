"""
maix.protocol module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['CMD', 'FLAGS', 'HEADER', 'MSG', 'Protocol', 'VERSION', 'crc16_IBM']
class CMD:
    """
    Members:
    
      CMD_APP_MAX
    
      CMD_SET_REPORT
    
      CMD_APP_LIST
    
      CMD_START_APP
    
      CMD_EXIT_APP
    
      CMD_CUR_APP_INFO
    
      CMD_APP_INFO
    
      CMD_KEY
    
      CMD_TOUCH
    """
    CMD_APP_INFO: typing.ClassVar[CMD]  # value = <CMD.CMD_APP_INFO: 253>
    CMD_APP_LIST: typing.ClassVar[CMD]  # value = <CMD.CMD_APP_LIST: 249>
    CMD_APP_MAX: typing.ClassVar[CMD]  # value = <CMD.CMD_APP_MAX: 200>
    CMD_CUR_APP_INFO: typing.ClassVar[CMD]  # value = <CMD.CMD_CUR_APP_INFO: 252>
    CMD_EXIT_APP: typing.ClassVar[CMD]  # value = <CMD.CMD_EXIT_APP: 251>
    CMD_KEY: typing.ClassVar[CMD]  # value = <CMD.CMD_KEY: 254>
    CMD_SET_REPORT: typing.ClassVar[CMD]  # value = <CMD.CMD_SET_REPORT: 248>
    CMD_START_APP: typing.ClassVar[CMD]  # value = <CMD.CMD_START_APP: 250>
    CMD_TOUCH: typing.ClassVar[CMD]  # value = <CMD.CMD_TOUCH: 255>
    __members__: typing.ClassVar[dict[str, CMD]]  # value = {'CMD_APP_MAX': <CMD.CMD_APP_MAX: 200>, 'CMD_SET_REPORT': <CMD.CMD_SET_REPORT: 248>, 'CMD_APP_LIST': <CMD.CMD_APP_LIST: 249>, 'CMD_START_APP': <CMD.CMD_START_APP: 250>, 'CMD_EXIT_APP': <CMD.CMD_EXIT_APP: 251>, 'CMD_CUR_APP_INFO': <CMD.CMD_CUR_APP_INFO: 252>, 'CMD_APP_INFO': <CMD.CMD_APP_INFO: 253>, 'CMD_KEY': <CMD.CMD_KEY: 254>, 'CMD_TOUCH': <CMD.CMD_TOUCH: 255>}
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
class FLAGS:
    """
    Members:
    
      FLAG_REQ
    
      FLAG_RESP
    
      FLAG_IS_RESP_MASK
    
      FLAG_RESP_OK
    
      FLAG_RESP_ERR
    
      FLAG_RESP_OK_MASK
    
      FLAG_REPORT
    
      FLAG_REPORT_MASK
    
      FLAG_VERSION_MASK
    """
    FLAG_IS_RESP_MASK: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_RESP: 128>
    FLAG_REPORT: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_REPORT: 32>
    FLAG_REPORT_MASK: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_REPORT: 32>
    FLAG_REQ: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_REQ: 0>
    FLAG_RESP: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_RESP: 128>
    FLAG_RESP_ERR: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_REQ: 0>
    FLAG_RESP_OK: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_RESP_OK: 64>
    FLAG_RESP_OK_MASK: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_RESP_OK: 64>
    FLAG_VERSION_MASK: typing.ClassVar[FLAGS]  # value = <FLAGS.FLAG_VERSION_MASK: 3>
    __members__: typing.ClassVar[dict[str, FLAGS]]  # value = {'FLAG_REQ': <FLAGS.FLAG_REQ: 0>, 'FLAG_RESP': <FLAGS.FLAG_RESP: 128>, 'FLAG_IS_RESP_MASK': <FLAGS.FLAG_RESP: 128>, 'FLAG_RESP_OK': <FLAGS.FLAG_RESP_OK: 64>, 'FLAG_RESP_ERR': <FLAGS.FLAG_REQ: 0>, 'FLAG_RESP_OK_MASK': <FLAGS.FLAG_RESP_OK: 64>, 'FLAG_REPORT': <FLAGS.FLAG_REPORT: 32>, 'FLAG_REPORT_MASK': <FLAGS.FLAG_REPORT: 32>, 'FLAG_VERSION_MASK': <FLAGS.FLAG_VERSION_MASK: 3>}
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
class MSG:
    body_len: int
    cmd: int
    has_been_replied: bool
    is_report: bool
    is_req: bool
    is_resp: bool
    resp_ok: int
    version: int
    @staticmethod
    def encode_report(*args, **kwargs):
        """
        Encode proactively report message
        
        Args:
          - body: report body, can be null
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    @staticmethod
    def encode_resp_err(*args, **kwargs):
        """
        Encode response error message
        
        Args:
          - code: error code
          - msg: error message
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    @staticmethod
    def encode_resp_ok(*args, **kwargs):
        """
        Encode response ok(success) message
        
        Args:
          - body: response body, can be null
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    @staticmethod
    def get_body(*args, **kwargs):
        """
        Get message body
        
        Returns: message body, bytes type
        """
    def set_body(self, body_new: maix.Bytes(bytes)) -> None:
        """
        Update message body
        
        Args:
          - body_new: new body data
        """
class Protocol:
    @staticmethod
    def encode_report(*args, **kwargs):
        """
        Encode proactively report message to buffer
        
        Args:
          - cmd: CMD value
          - body: report body, can be null
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    @staticmethod
    def encode_resp_err(*args, **kwargs):
        """
        Encode response error message to buffer
        
        Args:
          - cmd: CMD value
          - code: error code
          - msg: error message
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    @staticmethod
    def encode_resp_ok(*args, **kwargs):
        """
        Encode response ok(success) message to buffer
        
        Args:
          - cmd: CMD value
          - body: response body, can be null
        
        
        Returns: encoded data, if nullptr, means error, and the error code is -err.Err
        """
    def __init__(self, buff_size: int = 1024, header: int = 3148663466) -> None:
        ...
    def buff_size(self) -> int:
        """
        Data queue buffer size
        """
    def decode(self, new_data: maix.Bytes(bytes) = None) -> MSG:
        """
        Decode data in data queue and return a message
        
        Args:
          - new_data: new data add to data queue, if null, only decode.
        
        
        Returns: decoded message, if nullptr, means no message decoded.
        """
    def push_data(self, new_data: maix.Bytes(bytes)) -> maix._maix.err.Err:
        """
        Add data to data queue
        
        Args:
          - new_data: new data
        
        
        Returns: error code, maybe err.Err.ERR_BUFF_FULL
        """
def crc16_IBM(data: maix.Bytes(bytes)) -> int:
    """
    CRC16-IBM
    
    Args:
      - data: data, bytes type.
    
    
    Returns: CRC16-IBM value, uint16_t type.
    """
HEADER: int = 3148663466
VERSION: int = 1
