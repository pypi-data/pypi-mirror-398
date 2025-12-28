"""
maix.fs module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['File', 'SEEK', 'abspath', 'basename', 'dirname', 'exists', 'getcwd', 'getsize', 'isabs', 'isdir', 'isfile', 'islink', 'join', 'listdir', 'mkdir', 'open', 'realpath', 'remove', 'rename', 'rmdir', 'splitext', 'symlink', 'sync', 'tempdir']
class File:
    def __init__(self, path: str = '', mode: str = 'r') -> None:
        ...
    def close(self) -> None:
        """
        Close a file.
        """
    def eof(self) -> int:
        """
        End of file or not
        
        Returns: 0 if not reach end of file, else eof.
        """
    def flush(self) -> maix._maix.err.Err:
        """
        Flush file, ensure data is written to kernel buffer.
        
        Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
        """
    def open(self, path: str, mode: str) -> maix._maix.err.Err:
        """
        Open a file
        
        Args:
          - path: path to open
          - mode: open mode, support "r", "w", "a", "r+", "w+", "a+", "rb", "wb", "ab", "rb+", "wb+", "ab+"
        
        
        Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
        """
    def read(self, size: int) -> list[int]:
        """
        Read data from file API2
        
        Args:
          - size: max read size
        
        
        Returns: bytes data if success(need delete manually in C/C++), nullptr if failed
        """
    def readline(self) -> str:
        """
        Read line from file
        
        Returns: line if success, None(nullptr in C++) if failed. You need to delete the returned object manually in C/C++.
        """
    def seek(self, offset: int, whence: int) -> int:
        """
        Seek file position
        
        Args:
          - offset: offset to seek
          - whence: @see maix.fs.SEEK
        
        
        Returns: new position if success, -err::Err code if failed
        """
    def size(self) -> int:
        """
        Get file size
        
        Returns: file size if success, -err::Err code if failed
        """
    def sync(self) -> maix._maix.err.Err:
        """
        Sync file, ensure data is written to disk.
        
        Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
        """
    def tell(self) -> int:
        """
        Get file position
        
        Returns: file position if success, -err::Err code if failed
        """
    def write(self, buf: list[int]) -> int:
        """
        Write data to file API2
        
        Args:
          - buf: buffer to write
        
        
        Returns: write size if success, -err::Err code if failed
        """
class SEEK:
    """
    Members:
    
      FS_SEEK_SET
    
      FS_SEEK_CUR
    
      FS_SEEK_END
    """
    FS_SEEK_CUR: typing.ClassVar[SEEK]  # value = <SEEK.FS_SEEK_CUR: 1>
    FS_SEEK_END: typing.ClassVar[SEEK]  # value = <SEEK.FS_SEEK_END: 2>
    FS_SEEK_SET: typing.ClassVar[SEEK]  # value = <SEEK.FS_SEEK_SET: 0>
    __members__: typing.ClassVar[dict[str, SEEK]]  # value = {'FS_SEEK_SET': <SEEK.FS_SEEK_SET: 0>, 'FS_SEEK_CUR': <SEEK.FS_SEEK_CUR: 1>, 'FS_SEEK_END': <SEEK.FS_SEEK_END: 2>}
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
def abspath(path: str) -> str:
    """
    Get absolute path
    
    Args:
      - path: path to get absolute path
    
    
    Returns: absolute path if success, empty string if failed
    """
def basename(path: str) -> str:
    """
    Get base name of path
    
    Args:
      - path: path to get basename
    
    
    Returns: basename if success, empty string if failed
    """
def dirname(path: str) -> str:
    """
    Get directory name of path
    
    Args:
      - path: path to get dirname
    
    
    Returns: dirname if success, empty string if failed
    """
def exists(path: str) -> bool:
    """
    Check if the path exists
    
    Args:
      - path: path to check
    
    
    Returns: true if path exists
    """
def getcwd() -> str:
    """
    Get current working directory
    
    Returns: current working directory absolute path
    """
def getsize(path: str) -> int:
    """
    Get file size
    
    Args:
      - path: path to get size
    
    
    Returns: file size if success, -err::Err code if failed
    """
def isabs(path: str) -> bool:
    """
    Check if the path is absolute path
    
    Args:
      - path: path to check
    
    
    Returns: true if path is absolute path
    """
def isdir(path: str) -> bool:
    """
    Check if the path is a directory, if not exist, throw exception
    
    Args:
      - path: path to check
    
    
    Returns: true if path is a directory
    """
def isfile(path: str) -> bool:
    """
    Check if the path is a file, if not exist, throw exception
    
    Args:
      - path: path to check
    
    
    Returns: true if path is a file
    """
def islink(path: str) -> bool:
    """
    Check if the path is a link, if not exist, throw exception
    
    Args:
      - path: path to check
    
    
    Returns: true if path is a link
    """
def join(paths: list[str]) -> str:
    """
    Join paths
    
    Args:
      - paths: paths to join
    
    
    Returns: joined path if success, empty string if failed
    """
def listdir(path: str, recursive: bool = False, full_path: bool = False) -> list[str]:
    """
    List files in directory
    
    Args:
      - path: path to list
      - recursive: if true, list recursively, otherwise, only list current directory, default is false
      - full_path: if true, return full path, otherwise, only return basename, default is false
    
    
    Returns: files list if success, nullptr if failed, you should manually delete it in C++.
    """
def mkdir(path: str, exist_ok: bool = True, recursive: bool = True) -> maix._maix.err.Err:
    """
    Create a directory recursively
    
    Args:
      - path: path to create
      - exist_ok: if true, also return true if directory already exists
      - recursive: if true, create directory recursively, otherwise, only create one directory, default is true
    
    
    Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
    """
def open(path: str, mode: str) -> File:
    """
    Open a file, and return a File object
    
    Args:
      - path: path to open
      - mode: open mode, support "r", "w", "a", "r+", "w+", "a+", "rb", "wb", "ab", "rb+", "wb+", "ab+"
    
    
    Returns: File object if success(need to delete object manually in C/C++), nullptr if failed
    """
def realpath(path: str) -> str:
    """
    Get realpath of path
    
    Args:
      - path: path to get realpath
    
    
    Returns: realpath if success, empty string if failed
    """
def remove(path: str) -> maix._maix.err.Err:
    """
    Remove a file
    
    Args:
      - path: path to remove
    
    
    Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
    """
def rename(src: str, dst: str) -> maix._maix.err.Err:
    """
    Rename a file or directory
    
    Args:
      - src: source path
      - dst: destination path, if destination dirs not exist, will auto create
    
    
    Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
    """
def rmdir(path: str, recursive: bool = False) -> maix._maix.err.Err:
    """
    Remove a directory
    
    Args:
      - path: path to remove
      - recursive: if true, remove directory recursively, otherwise, only remove empty directory, default is false
    
    
    Returns: err::ERR_NONE(err.Err.ERR_NONE in MaixPy) if success, other error code if failed
    """
def splitext(path: str) -> list[str]:
    """
    Get file extension
    
    Args:
      - path: path to get extension
    
    
    Returns: prefix_path and extension list if success, empty string if failed
    """
def symlink(src: str, link: str, force: bool = False) -> maix._maix.err.Err:
    """
    Create soft link
    
    Args:
      - src: real file path
      - link: link file path
      - force: force link, if already have link file, will delet it first then create.
    """
def sync() -> None:
    """
    Sync files, ensure they're wrriten to disk from RAM
    """
def tempdir() -> str:
    """
    Get temp files directory
    
    Returns: temp files directory
    """
