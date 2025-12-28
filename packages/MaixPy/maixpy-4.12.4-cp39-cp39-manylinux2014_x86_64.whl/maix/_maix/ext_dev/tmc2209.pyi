"""
maix.ext_dev.tmc2209 module
"""
from __future__ import annotations
import typing
__all__: list[str] = ['ScrewSlide', 'Slide', 'slide_scan', 'slide_test']
class ScrewSlide:
    def __init__(self, port: str, addr: int, baud: int, step_angle: float, micro_step: int, screw_pitch: float, speed_mm_s: float = -1, use_internal_sense_resistors: bool = True, run_current_per: int = 100, hold_current_per: int = 100) -> None:
        ...
    def hold_current_per(self, per: int = -1) -> int:
        """
        Get or set the hold current percentage
        
        Args:
          - per: Hold current percentage, range 0~100(%). Default is -1, indicating no change and returning the current hold current percentage.
        
        
        Returns: int Current hold current percentage if per is -1, otherwise the new set percentage.
        """
    def move(self, oft: float, speed_mm_s: int = -1, callback: typing.Callable[[float], bool] = None) -> None:
        """
        Move the slide by a specified length
        
        Args:
          - oft: Length to move, 10 means 10mm, float type.
        Positive values move the slide in the positive direction, negative values move it in the opposite direction.
          - speed_mm_s: Speed in mm/s. Default is -1, indicating the use of the default speed set during initialization.
          - callback: Callback function to be called during movement.
        The callback function receives the current progress percentage (0~100%) of the movement.
        If the callback returns true, the move operation will be terminated immediately. Default is nullptr.
        """
    def reset(self, callback: typing.Callable[[], bool], dir: bool = False, speed_mm_s: int = -1) -> None:
        """
        Reset the slide position
        
        Args:
          - callback: Callback function to be called during the reset loop.
        The reset operation will only terminate if the callback returns true.
          - dir: Direction of reset. Default is false.
          - speed_mm_s: Speed in mm/s. Default is -1, indicating the use of the speed set during initialization.
        """
    def run_current_per(self, per: int = -1) -> int:
        """
        Get or set the run current percentage
        
        Args:
          - per: Run current percentage, range 0~100(%).
        Default is -1, indicating no change and returning the current run current percentage.
        
        
        Returns: int Current run current percentage if per is -1, otherwise the new set percentage.
        """
    def use_internal_sense_resistors(self, b: bool = True) -> None:
        """
        Enable or disable internal sense resistors
        
        Args:
          - b: Boolean value to enable (true) or disable (false) internal sense resistors. Default is true.
        """
class Slide:
    def __init__(self, port: str, addr: int, baud: int, step_angle: float, micro_step: int, round_mm: float, speed_mm_s: float = -1, use_internal_sense_resistors: bool = True, run_current_per: int = 100, hold_current_per: int = 100, cfg_file_path: str = '') -> None:
        ...
    def hold_current_per(self, per: int = -1) -> int:
        """
        Get or set the hold current percentage
        Retrieves or sets the hold current percentage. If the parameter is -1, it returns the current setting.
        
        Args:
          - per: Hold current percentage, range 0~100(%), integer type. Default is -1, indicating no change.
        
        
        Returns: int Current hold current percentage if per is -1, otherwise the new set percentage.
        """
    def load_conf(self, path: str) -> None:
        """
        Load configuration from a file
        Loads the configuration settings for the slide from the specified file path.
        
        Args:
          - path: Path to the configuration file, string type.
        """
    def move(self, oft: float, speed_mm_s: int = -1, check: bool = True) -> None:
        """
        Move the slide by a specified length
        Moves the slide by the specified length at the given speed. Optionally checks for stall conditions.
        
        Args:
          - oft: Length to move, float type.
          - speed_mm_s: Speed in mm/s. Default is -1, indicating the use of the default speed set during initialization.
          - check: Enable movement check if true, boolean type. Default is true.
        """
    def reset(self, dir: bool = False, speed_mm_s: int = -1) -> None:
        """
        Reset the slide position
        Resets the slide position in the specified direction at the given speed.
        
        Args:
          - dir: Direction of reset, boolean type. Default is false.
          - speed_mm_s: Speed in mm/s. Default is -1, indicating the use of the speed set during initialization.
        """
    def run_current_per(self, per: int = -1) -> int:
        """
        Get or set the run current percentage
        Retrieves or sets the run current percentage. If the parameter is -1, it returns the current setting.
        
        Args:
          - per: Run current percentage, range 0~100(%), integer type. Default is -1, indicating no change.
        
        
        Returns: int Current run current percentage if per is -1, otherwise the new set percentage.
        """
    def stop_default_per(self, per: int = -1) -> int:
        """
        Get or set the stop default percentage
        Retrieves or sets the stop default percentage. If the parameter is -1, it returns the current setting.
        
        Args:
          - per: Stop default percentage, range 0~100(%), integer type. Default is -1, indicating no change.
        
        
        Returns: int Current stop default percentage if per is -1, otherwise the new set percentage.
        """
    def use_internal_sense_resistors(self, b: bool = True) -> None:
        """
        Enable or disable internal sense resistors
        Enables or disables the internal sense resistors based on the provided boolean value.
        
        Args:
          - b: Boolean value to enable (true) or disable (false) internal sense resistors. Default is true.
        """
def slide_scan(port: str, addr: int, baud: int, step_angle: float, micro_step: int, round_mm: float, speed_mm_s: float, dir: bool = True, use_internal_sense_resistors: bool = True, run_current_per: int = 100, hold_current_per: int = 100, conf_save_path: str = './slide_conf.bin', force_update: bool = True) -> None:
    """
    Scan and initialize the slide with the given parameters
    
    Args:
      - port: UART port, string type.
      - addr: TMC2209 UART address, range 0x00~0x03, integer type.
      - baud: UART baud rate, integer type.
      - step_angle: Motor step angle, float type.
      - micro_step: Motor micro step, options: 1/2/4/8/16/32/64/128/256, integer type.
      - round_mm: Round distance in mm, float type.
      - speed_mm_s: Speed of the slide in mm/s, float type.
      - dir: Direction of movement, boolean type. Default is true.
      - use_internal_sense_resistors: Enable internal sense resistors if true, disable if false, boolean type. Default is true.
      - run_current_per: Motor run current percentage, range 0~100(%), integer type. Default is 100%.
      - hold_current_per: Motor hold current percentage, range 0~100(%), integer type. Default is 100%.
      - conf_save_path: Configuration save path, string type. Default is "./slide_conf.bin".
      - force_update: Force update the configuration if true, boolean type. Default is true.
    """
def slide_test(port: str, addr: int, baud: int, step_angle: float, micro_step: int, round_mm: float, speed_mm_s: float, dir: bool = True, use_internal_sense_resistors: bool = True, run_current_per: int = 100, hold_current_per: int = 100, conf_save_path: str = './slide_conf.bin') -> None:
    """
    Test the slide with the given parameters
    This function tests the slide by moving it in the specified direction until a stall condition is detected, as defined in the configuration file.
    
    Args:
      - port: UART port, string type.
      - addr: TMC2209 UART address, range 0x00~0x03, integer type.
      - baud: UART baud rate, integer type.
      - step_angle: Motor step angle, float type.
      - micro_step: Motor micro step, options: 1/2/4/8/16/32/64/128/256, integer type.
      - round_mm: Round distance in mm, float type.
      - speed_mm_s: Speed of the slide in mm/s, float type.
      - dir: Direction of movement, boolean type. Default is true.
      - use_internal_sense_resistors: Enable internal sense resistors if true, disable if false, boolean type. Default is true.
      - run_current_per: Motor run current percentage, range 0~100(%), integer type. Default is 100%.
      - hold_current_per: Motor hold current percentage, range 0~100(%), integer type. Default is 100%.
      - conf_save_path: Configuration save path, string type. Default is "./slide_conf.bin".
    """
