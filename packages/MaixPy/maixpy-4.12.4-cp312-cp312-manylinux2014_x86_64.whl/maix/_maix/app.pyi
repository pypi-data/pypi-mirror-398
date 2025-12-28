"""
maix.app module
"""
from __future__ import annotations
import maix._maix.err
__all__: list[str] = ['APP_Info', 'Version', 'app_id', 'get_app_config_kv', 'get_app_config_path', 'get_app_data_path', 'get_app_info', 'get_app_path', 'get_apps_info', 'get_apps_info_path', 'get_exit_msg', 'get_font_path', 'get_icon_path', 'get_picture_path', 'get_share_path', 'get_start_param', 'get_sys_config_kv', 'get_tmp_path', 'get_video_path', 'have_exit_msg', 'need_exit', 'running', 'set_app_config_kv', 'set_app_id', 'set_exit_flag', 'set_exit_msg', 'set_sys_config_kv', 'switch_app']
class APP_Info:
    author: str
    desc: str
    descs: dict[str, str]
    exec: str
    icon: str
    id: str
    name: str
    names: dict[str, str]
    version: Version
class Version:
    @staticmethod
    def from_str(version_str: str) -> Version:
        """
        Convert from string, e.g. "1.0.0"
        """
    def __str__(self) -> str:
        """
        Convert to string, e.g. 1.0.0
        """
def app_id() -> str:
    """
    Get current APP ID.
    
    Returns: APP ID.
    """
def get_app_config_kv(item: str, key: str, value: str = '', from_cache: bool = True) -> str:
    """
    Get APP config item value.
    
    Args:
      - item: name of setting item, e.g. user_info
      - key: config key, e.g. for user_info, key can be name, age etc.
      - value: default value, if not found, return this value.
      - from_cache: if true, read from cache, if false, read from file.
    
    
    Returns: config value, always string type, if not found, return empty string.
    """
def get_app_config_path() -> str:
    """
    Get APP config path, ini format, so you can use your own ini parser to parse it like `configparser` in Python.
    All APP config info is recommended to store in this file.
    
    Returns: APP config path(ini format).
    """
def get_app_data_path() -> str:
    """
    Get APP info, APP can store private data in this directory.
    
    Returns: APP data path "./data", just return the data folder in current path because APP executed in app install path or project path.
    So, you must execute your program in you project path to use the project/data folder when you debug your APP.
    """
def get_app_info(app_id: str) -> APP_Info:
    """
    Get app info by app id.
    
    Returns: app.APP_Info type.
    """
def get_app_path(app_id: str = '') -> str:
    """
    Get APP path.
    
    Args:
      - app_id: APP ID, if empty, return current APP path, else return the APP path by app_id.
    
    
    Returns: APP path, just return the current path because APP executed in app install path or project path.
    So, you must execute your program in you project path to use the project/data folder when you debug your APP.
    """
def get_apps_info(ignore_launcher: bool = False, ignore_app_store: bool = False) -> list[APP_Info]:
    """
    Get APP info list.
    
    Args:
      - ignore_launcher: if true, ignore launcher APP. default false.
      - ignore_app_store: if true, ignore app store APP. default false.
    
    
    Returns: APP info list. APP_Info object list.
    """
def get_apps_info_path() -> str:
    """
    Get APP info file path.
    """
def get_exit_msg(cache: bool = False) -> tuple[str, maix._maix.err.Err, str]:
    """
    Get APP exit code and exit message.
    
    Args:
      - cache: if true, read from cache, if false, read from file. default false.
    
    
    Returns: exit return app_id, exit code and exit message.
    """
def get_font_path() -> str:
    """
    Get font path of share, shared font will put in this directory
    
    Returns: share font path.
    """
def get_icon_path() -> str:
    """
    Get icon path of share, shared icon will put in this directory
    
    Returns: share icon path.
    """
def get_picture_path() -> str:
    """
    Get picture path of share, shared picture will put in this directory
    
    Returns: share picture path.
    """
def get_share_path() -> str:
    """
    Get data path of share, shared data like picture and video will put in this directory
    
    Returns: share data path.
    """
def get_start_param() -> str:
    """
    Get start param set by caller
    
    Returns: param, string type
    """
def get_sys_config_kv(item: str, key: str, value: str = '', from_cache: bool = True) -> str:
    """
    Get system config item value.
    You can find all supported config items in https://wiki.sipeed.com/maixpy/doc/zh/basic/app.html .
    
    Args:
      - item: name of setting item, e.g. wifi, language. more see settings APP.
      - key: config key, e.g. for wifi, key can be ssid, for language, key can be locale.
      - value: default value, if not found, return this value.
      - from_cache: if true, read from cache, if false, read from file.
    
    
    Returns: config value, always string type, if not found, return empty string.
    """
def get_tmp_path() -> str:
    """
    Get global temporary data path, APPs can use this path as temporary data directory.
    
    Returns: temporary data path.
    """
def get_video_path() -> str:
    """
    Get video path of share, shared video will put in this directory
    
    Returns: share video path.
    """
def have_exit_msg(cache: bool = False) -> bool:
    """
    Check if have exit msg
    
    Args:
      - cache: if true, just check from cache, if false, check from file. default false.
    
    
    Returns: true if have exit msg, false if not.
    """
def need_exit() -> bool:
    """
    Shoule this APP exit?
    
    Returns: true if this APP should exit, false if not.
    """
def running() -> bool:
    """
    App should running? The same as !app::need_exit() (not app::need_exit() in MaixPy).
    
    Returns: true if this APP should running, false if not.
    """
def set_app_config_kv(item: str, key: str, value: str, write_file: bool = True) -> maix._maix.err.Err:
    """
    Set APP config item value.
    
    Args:
      - item: name of setting item, e.g. user_info
      - key: config key, e.g. for user_info, key can be name, age etc.
      - value: config value, always string type.
      - write_file: if true, write to file, if false, just write to cache.
    
    
    Returns: err::Err
    """
def set_app_id(app_id: str) -> str:
    """
    Set current APP ID.
    
    Args:
      - app_id: APP ID.
    """
def set_exit_flag(exit: bool) -> None:
    """
    Set exit flag. You can get exit flag by app.need_exit().
    
    Args:
      - exit: true if this APP should exit, false if not.
    """
def set_exit_msg(code: maix._maix.err.Err, msg: str) -> maix._maix.err.Err:
    """
    Set APP exit code and exit message.
    If code != 0, the launcher will show a dialog to user, and display the msg.
    
    Args:
      - code: exit code, 0 means success, other means error, if code is 0, do nothing.
      - msg: exit message, if code is 0, msg is not used.
    
    
    Returns: exit code, the same as arg @code.
    """
def set_sys_config_kv(item: str, key: str, value: str, write_file: bool = True) -> maix._maix.err.Err:
    """
    Set system config item value.
    """
def switch_app(app_id: str, idx: int = -1, start_param: str = '') -> None:
    """
    Exit this APP and start another APP(by launcher).
    Call this API will call set_exit_flag(true), you should check app::need_exit() in your code.
    And exit this APP if app::need_exit() return true.
    
    Args:
      - app_id: APP ID which will be started. app_id and idx must have one is valid.
      - idx: APP index. app_id and idx must have one is valid.
      - start_param: string type, will send to app, app can get this param by `app.get_start_param()`
    """
