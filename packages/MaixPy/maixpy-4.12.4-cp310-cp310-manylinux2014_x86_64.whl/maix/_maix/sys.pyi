"""
maix.sys module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Feature', 'bytes_to_human', 'cpu_freq', 'cpu_temp', 'cpu_usage', 'device_configs', 'device_id', 'device_key', 'device_name', 'disk_partitions', 'disk_usage', 'host_domain', 'host_name', 'ip_address', 'is_support', 'mac_address', 'maixpy_version', 'memory_info', 'npu_freq', 'npu_usage', 'os_version', 'poweroff', 'reboot', 'register_default_signal_handle', 'runtime_version']
class Feature:
    """
    Members:
    
      AI_ISP
    
      MAX
    """
    AI_ISP: typing.ClassVar[Feature]  # value = <Feature.AI_ISP: 0>
    MAX: typing.ClassVar[Feature]  # value = <Feature.MAX: 1>
    __members__: typing.ClassVar[dict[str, Feature]]  # value = {'AI_ISP': <Feature.AI_ISP: 0>, 'MAX': <Feature.MAX: 1>}
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
def bytes_to_human(bytes: int, precision: int = 2, base: int = 1024, units: list[str] = [], sep: str = ' ') -> str:
    """
    Bytes to human readable string
    
    Args:
      - bytes:: bytes size，e.g. 1234B = 1234/1024 = 1.205 KB
      - precision:: decimal precision, default 2
      - base:: base number, default 1024
      - unit:: unit string, e.g. "B"
      - sep:: separator string, e.g. " "
    
    
    Returns: human readable string, e.g. "1.21 KB"
    """
def cpu_freq() -> dict[str, int]:
    """
    Get CPU frequency
    
    Returns: CPU frequency, dict type, e.g. {"cpu0": 1000000000, "cpu1": 1000000000}
    """
def cpu_temp() -> dict[str, float]:
    """
    Get CPU temperature
    
    Returns: CPU temperature, unit dgree, dict type, e.g. {"cpu": 50.0, "cpu0": 50, "cpu1": 50}
    """
def cpu_usage() -> dict[str, float]:
    """
    Get CPU usage
    
    Returns: CPU usage, dict type, e.g. {"cpu": 50.0, "cpu0": 50, "cpu1": 50}
    """
def device_configs(cache: bool = True) -> dict[str, str]:
    """
    Get device configs, we also say board configs. e.g. for MaixCAM it read form /boot/board
    
    Args:
      - cache: read config from cache(if exists, or will call device_configs first internally) if true,
    if false, always read fron config file.
    
    
    Returns: device config,json format
    """
def device_id(cache: bool = True) -> str:
    """
    Get device id
    
    Args:
      - cache: read id from cache(if exists, or will call device_configs first internally) if true,
    if false, always read fron config file.
    
    
    Returns: device id, e.g. "maixcam" "maixcam_pro"
    """
def device_key() -> str:
    """
    Get device key, can be unique id of device
    
    Returns: device key, 32 bytes hex string, e.g. "1234567890abcdef1234567890abcdef"
    """
def device_name(cache: bool = True) -> str:
    """
    Get device name
    
    Args:
      - cache: read id from cache(if exists, or will call device_configs first internally) if true,
    if false, always read fron config file.
    
    
    Returns: device name, e.g. "MaixCAM" "MaixCAM-Pro"
    """
def disk_partitions(only_disk: bool = True) -> list[dict[str, str]]:
    """
    Get disk partition and mount point info
    
    Args:
      - only_disk: only return real disk, tempfs sysfs etc. not return, default true.
    
    
    Returns: disk partition and mount point info, list type, e.g. [{"device": "/dev/mmcblk0p1", "mountpoint": "/mnt/sdcard", "fstype": "vfat"}]
    """
def disk_usage(path: str = '/') -> dict[str, int]:
    """
    Get disk usage
    
    Args:
      - path:: disk path, default "/"
    
    
    Returns: disk usage, dict type, e.g. {"total": 1024, "used": 512}
    """
def host_domain() -> str:
    """
    Get host domain
    
    Returns: host domain, e.g. "maixcam-2f9f.local"
    """
def host_name() -> str:
    """
    Get host name
    
    Returns: host name, e.g. "maixcam-2f9f"
    """
def ip_address() -> dict[str, str]:
    """
    Get ip address
    
    Returns: ip address, dict type, e.g. {"eth0": "192.168.0.195", "wlan0": "192.168.0.123", "usb0": "10.47.159.1"}
    """
def is_support(feature: Feature) -> bool:
    """
    Query is board support special feature or not.
    
    Args:
      - feature: which feature you want to query, see sys.Feature enumerate.
    """
def mac_address() -> dict[str, str]:
    """
    Get mac address
    
    Returns: mac address, dict type, e.g. {"eth0": "00:0c:29:2f:9f:00", "wlan0": "00:0c:29:2f:9f:01", "usb0": "00:0c:29:2f:9f:02"}
    """
def maixpy_version() -> str:
    """
    Get MaixPy version, if get failed will return empty string.
    
    Returns: version  string, e.g. "4.4.21"
    """
def memory_info() -> dict[str, int]:
    """
    Get memory info
    
    Returns: memory info, dict type, e.g. {"total": 1024, "used": 512, "hw_total": 256*1024*1024}
    total: total memory size in Byte.
    used: used memory size in Byte.
    hw_total: total memory size in Byte of hardware, the total <= hw_total，
    OS kernel may reserve some memory for some hardware like camera, npu, display etc.
    cmm_total: Board or Chip custom memory management area, we call them cmm memory here. For example, for MaixCAM is IOA, for MaixCAM2 is CMM.
    cmm_used: Board or Chip custom memory management area used size, we call them cmm memory here.
    cma_total: Contiguous Memory Allocator (Linux CMA standard) total size in Byte.
    cma_used: Contiguous Memory Allocator (Linux CMA standard) used size in Byte.
    """
def npu_freq() -> dict[str, int]:
    """
    Get NPU frequency
    
    Returns: NPU frequency, dict type, e.g. {"npu0": 500000000}, value -1 means not support query on this platform.
    If get from system failed, will return last time value.
    """
def npu_usage() -> dict[str, float]:
    """
    Get NPU usage
    
    Returns: NPU usage, dict type, e.g. {"npu": 50.0, "npu0": 50, "npu1": 50}
    """
def os_version() -> str:
    """
    Get system version
    
    Returns: version string, e.g. "maixcam-2024-08-13-maixpy-v4.4.20"
    """
def poweroff() -> None:
    """
    Power off device
    """
def reboot() -> None:
    """
    Power off device and power on
    """
def register_default_signal_handle() -> None:
    """
    register default signal handle
    """
def runtime_version() -> str:
    """
    Get runtime version
    
    Returns: current runtime version
    """
