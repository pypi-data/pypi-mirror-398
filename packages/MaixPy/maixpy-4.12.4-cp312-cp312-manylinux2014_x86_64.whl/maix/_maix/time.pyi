"""
maix.time module
"""
from __future__ import annotations
from maix.__maix_time__ import sleep_ms
from maix.__maix_time__ import sleep_us
from time import sleep
__all__: list[str] = ['DateTime', 'FPS', 'fps', 'fps_set_buff_len', 'fps_start', 'gmtime', 'list_timezones', 'localtime', 'now', 'ntp_sync_sys_time', 'ntp_sync_sys_time_with_config', 'ntp_timetuple', 'ntp_timetuple_with_config', 'sleep', 'sleep_ms', 'sleep_us', 'strptime', 'ticks_diff', 'ticks_ms', 'ticks_s', 'ticks_us', 'time', 'time_diff', 'time_ms', 'time_s', 'time_us', 'timezone', 'timezone2']
class DateTime:
    day: int
    hour: int
    microsecond: int
    minute: int
    month: int
    second: int
    weekday: int
    year: int
    yearday: int
    zone: float
    zone_name: str
    def __init__(self, year: int = 0, month: int = 0, day: int = 0, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0, yearday: int = 0, weekday: int = 0, zone: int = 0) -> None:
        ...
    def strftime(self, format: str) -> str:
        """
        Convert to string
        
        Returns: date time string
        """
    def timestamp(self) -> float:
        """
        Convert to float timestamp
        
        Returns: float timestamp
        """
class FPS:
    def __init__(self, buff_len: int = 20) -> None:
        ...
    def end(self) -> float:
        """
        Calculate FPS since last call this method.
        FPS is average value of recent n(buff_len) times, and you can call fps_set_buff_len(10) to change buffer length, default is 20.
        Multiple invoke this function will calculate fps between two invoke, and you can also call fps_start() fisrt to manually assign fps calulate start point.
        
        Returns: float type, current fps since last call this method
        """
    def fps(self) -> float:
        """
        The same as end function.
        
        Returns: float type, current fps since last call this method
        """
    def set_buff_len(self, len: int) -> None:
        """
        Set fps method buffer length, by default the buffer length is 10.
        
        Args:
          - len: Buffer length to store recent fps value.
        """
    def start(self) -> None:
        """
        Manually set fps calculation start point, then you can call fps() function to calculate fps between start() and fps().
        """
def fps() -> float:
    """
    Calculate FPS since last call this method.
    Attention, this method is not multi thread safe, only call this method in one threads.
    If you want to use in multi threads, please use time.FPS class.
    FPS is average value of recent n(buff_len) times, and you can call fps_set_buff_len(10) to change buffer length, default is 20.
    Multiple invoke this function will calculate fps between two invoke, and you can also call fps_start() fisrt to manually assign fps calulate start point.
    
    Returns: float type, current fps since last call this method
    """
def fps_set_buff_len(len: int) -> None:
    """
    Set fps method buffer length, by default the buffer length is 10.
    
    Args:
      - len: Buffer length to store recent fps value.
    """
def fps_start() -> None:
    """
    Manually set fps calculation start point, then you can call fps() function to calculate fps between fps_start() and fps().
    """
def gmtime(timestamp: float) -> DateTime:
    """
    timestamp to DateTime(time zone is UTC (value 0))
    
    Args:
      - timestamp: double timestamp
    
    
    Returns: DateTime
    """
def list_timezones() -> dict[str, list[str]]:
    """
    List all timezone info
    
    Returns: A dict with key are regions, and value are region's cities.
    """
def localtime() -> DateTime:
    """
    Get local time
    
    Returns: local time, DateTime type
    """
def now() -> DateTime:
    """
    Get current UTC date and time
    
    Returns: current date and time, DateTime type
    """
def ntp_sync_sys_time(host: str, port: int = -1, retry: int = 3, timeout_ms: int = 0) -> list[int]:
    """
    Retrieves time from an NTP server and synchronizes the system time
    This function fetches the current time from the specified NTP server and port,
    then synchronizes the system time with the retrieved time.
    
    Args:
      - host: The hostname or IP address of the NTP server.
      - port: The port number of the NTP server. Use 123 for the default port.
      - retry: The number of retry attempts. Must be at least 1.
      - timeout_ms: The timeout duration in milliseconds. Must be non-negative.
    
    
    Returns: A list of 6 elements: [year, month, day, hour, minute, second]
    """
def ntp_sync_sys_time_with_config(path: str) -> list[int]:
    """
    Retrieves time from an NTP server using a configuration file and synchronizes the system time
    This function reads the configuration from a YAML file to fetch the current time
    from a list of specified NTP servers, then synchronizes the system time with the retrieved time.
    
    Args:
      - path: The path to the YAML configuration file, which should include:
    - Config:
    - retry: Number of retry attempts (must be at least 1)
    - total_timeout_ms: Total timeout duration in milliseconds (must be non-negative)
    - NtpServers:
    - host: Hostname or IP address of the NTP server
    - port: Port number of the NTP server (use 123 for default)
    Example YAML configuration:
    Config:
    - retry: 3
    - total_timeout_ms: 10000
    NtpServers:
    - host: "pool.ntp.org"
    port: 123
    - host: "time.nist.gov"
    port: 123
    - host: "time.windows.com"
    port: 123
    
    
    Returns: A vector of integers containing the time details: [year, month, day, hour, minute, second]
    """
def ntp_timetuple(host: str, port: int = -1, retry: int = 3, timeout_ms: int = 0) -> list[int]:
    """
    Retrieves time from an NTP server
    This function fetches the current time from the specified NTP server and port,
    returning a tuple containing the time details.
    
    Args:
      - host: The hostname or IP address of the NTP server.
      - port: The port number of the NTP server. Use -1 for the default port 123.
      - retry: The number of retry attempts. Must be at least 1.
      - timeout_ms: The timeout duration in milliseconds. Must be non-negative.
    
    
    Returns: A list of 6 elements: [year, month, day, hour, minute, second]
    """
def ntp_timetuple_with_config(path: str) -> list[int]:
    """
    Retrieves time from an NTP server using a configuration file
    This function reads the configuration from a YAML file to fetch the current time
    from a list of specified NTP servers, returning a tuple containing the time details.
    
    Args:
      - path: The path to the YAML configuration file, which should include:
    - Config:
    - retry: Number of retry attempts (must be at least 1)
    - total_timeout_ms: Total timeout duration in milliseconds (must be non-negative)
    - NtpServers:
    - host: Hostname or IP address of the NTP server
    - port: Port number of the NTP server (use 123 for default)
    Example YAML configuration:
    Config:
    - retry: 3
    - total_timeout_ms: 10000
    NtpServers:
    - host: "pool.ntp.org"
    port: 123
    - host: "time.nist.gov"
    port: 123
    - host: "time.windows.com"
    port: 123
    
    
    Returns: A list of 6 elements: [year, month, day, hour, minute, second]
    """
def strptime(str: str, format: str) -> DateTime:
    """
    DateTime from string
    
    Args:
      - str: date time string
      - format: date time format
    
    
    Returns: DateTime
    """
def ticks_diff(last: float, now: float = -1) -> float:
    """
    Calculate time difference in s.
    
    Args:
      - last: last time
      - now: current time, can be -1 if use current time
    
    
    Returns: time difference
    """
def ticks_ms() -> int:
    """
    Get current time in ms since bootup
    
    Returns: current time in ms, uint64_t type
    """
def ticks_s() -> float:
    """
    Get current time in s since bootup
    
    Returns: current time in s, double type
    """
def ticks_us() -> int:
    """
    Get current time in us since bootup
    
    Returns: current time in us, uint64_t type
    """
def time() -> float:
    """
    Get current time in s
    
    Returns: current time in s, double type
    """
def time_diff(last: float, now: float = -1) -> float:
    """
    Calculate time difference in s.
    
    Args:
      - last: last time
      - now: current time, can be -1 if use current time
    
    
    Returns: time difference
    """
def time_ms() -> int:
    """
    Get current time in ms
    
    Returns: current time in ms, uint64_t type
    """
def time_s() -> int:
    """
    Get current time in s
    
    Returns: current time in s, uint64_t type
    """
def time_us() -> int:
    """
    Get current time in us
    
    Returns: current time in us, uint64_t type
    """
def timezone(timezone: str = '') -> str:
    """
    Set or get timezone
    
    Args:
      - timezone: string type, can be empty and default to empty, if empty, only return crrent timezone, a "region/city" string, e.g. Asia/Shanghai, Etc/UTC, you can get all by list_timezones function.
    
    
    Returns: string type, return current timezone setting.
    """
def timezone2(region: str = '', city: str = '') -> list[str]:
    """
    Set or get timezone
    
    Args:
      - region: string type, which region to set, can be empty means only get current, default empty.
      - city: string type, which city to set, can be empty means only get current, default empty.
    
    
    Returns: list type, return current timezone setting, first is region, second is city.
    """
