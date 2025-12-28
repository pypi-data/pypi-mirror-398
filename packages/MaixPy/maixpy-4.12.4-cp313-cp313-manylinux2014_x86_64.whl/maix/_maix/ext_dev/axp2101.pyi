"""
maix.ext_dev.axp2101 module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['AXP2101', 'ChargerCurrent', 'ChargerStatus', 'PowerChannel', 'PowerOffTime', 'PowerOnTime']
class AXP2101:
    def __init__(self, i2c_bus: int = -1, addr: int = 52) -> None:
        ...
    def aldo1(self, voltage: int = -1) -> int:
        """
        Set and get the PMU ALDO1 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU ALDO1 voltage.
        """
    def aldo2(self, voltage: int = -1) -> int:
        """
        Set and get the PMU ALDO2 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU ALDO2 voltage.
        """
    def aldo3(self, voltage: int = -1) -> int:
        """
        Set and get the PMU ALDO3 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU ALDO3 voltage.
        """
    def aldo4(self, voltage: int = -1) -> int:
        """
        Set and get the PMU ALDO4 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU ALDO4 voltage.
        """
    def bldo1(self, voltage: int = -1) -> int:
        """
        Set and get the PMU BLDO1 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU BLDO1 voltage.
        """
    def bldo2(self, voltage: int = -1) -> int:
        """
        Set and get the PMU BLDO2 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~3500mV(step 100mV).
        
        
        Returns: int, return the PMU BLDO2 voltage.
        """
    def clean_irq(self) -> maix._maix.err.Err:
        """
        Clear interrupt flag.
        
        Returns: err::Err type, if clean success, return err::ERR_NONE.
        """
    def dcdc1(self, voltage: int = -1) -> int:
        """
        Set and get the PMU DCDC1 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 1500mV~3400mV(step 20mV).
        
        
        Returns: int, return the PMU DCDC1 voltage.
        """
    def dcdc2(self, voltage: int = -1) -> int:
        """
        Set and get the PMU DCDC2 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~1200mV(step 10mV) and 1220mV~1540mV(step 20mV).
        
        
        Returns: int, return the PMU DCDC2 voltage.
        """
    def dcdc3(self, voltage: int = -1) -> int:
        """
        Set and get the PMU DCDC3 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~1200mV(step 10mV) and 1220mV~1540mV(step 20mV).
        
        
        Returns: int, return the PMU DCDC3 voltage.
        """
    def dcdc4(self, voltage: int = -1) -> int:
        """
        Set and get the PMU DCDC4 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 500mV~1200mV(step 10mV) and 1220mV~1840mV(step 20mV).
        
        
        Returns: int, return the PMU DCDC4 voltage.
        """
    def dcdc5(self, voltage: int = -1) -> int:
        """
        Set and get the PMU DCDC5 voltage.
        
        Args:
          - voltage: The voltage to be set,
        voltage range is 1400mV~3700mV(step 100mV).
        
        
        Returns: int, return the PMU DCDC5 voltage.
        """
    def get_bat_charging_cur(self) -> ChargerCurrent:
        """
        Get the battery charging current.
        
        Returns: ChargerCurrent, return the currently set charging current.
        """
    def get_bat_percent(self) -> int:
        """
        Get the battery percentage.
        
        Returns: int type, return battery percentage.
        """
    def get_bat_vol(self) -> int:
        """
        Get the battery voltage.
        
        Returns: uint16_t type, return battery voltage.
        """
    def get_charger_status(self) -> ChargerStatus:
        """
        Get the battery charging status.
        
        Returns: int type, return battery charging status.
        """
    def get_poweroff_time(self) -> PowerOffTime:
        """
        Get power-off time.
        
        Returns: PowerOffTime, return power-off time.
        """
    def get_poweron_time(self) -> PowerOnTime:
        """
        Get power-on time.
        
        Returns: PowerOnTime, return power-on time.
        """
    def init(self) -> maix._maix.err.Err:
        """
        Initialise the AXP2101.
        
        Returns: err::Err type, if init success, return err::ERR_NONE.
        """
    def is_bat_connect(self) -> bool:
        """
        Is the battery connected.
        
        Returns: bool type, if battery is connected, return true.
        """
    def is_charging(self) -> bool:
        """
        Is bat charging.
        
        Returns: bool type, if bat is charging, return true.
        """
    def is_vbus_in(self) -> bool:
        """
        Is the power adapter connected.
        
        Returns: bool type, if power adapter is connected, return true.
        """
    def poweroff(self) -> maix._maix.err.Err:
        """
        Poweroff immediately.
        
        Returns: err::Err type, if init success, return err::ERR_NONE.
        """
    def set_bat_charging_cur(self, current: ChargerCurrent) -> maix._maix.err.Err:
        """
        Set the battery charging current.
        
        Args:
          - current: The current to be set.
        The available values are 0mA, 100mA, 125mA, 150mA, 175mA,
        200mA, 300mA, 400mA, 500mA, 600mA, 700mA, 800mA, 900mA, and 1000mA.
        
        
        Returns: err::Err type, if set success, return err::ERR_NONE.
        """
    def set_poweroff_time(self, tm: PowerOffTime) -> maix._maix.err.Err:
        """
        Set power-off time, The device will shut down
        if the power button is held down longer than this time.
        
        Args:
          - tm: The time to be set, you can set it to 4s, 6s, 8s, or 10s.
        
        
        Returns: err::Err type, if set success, return err::ERR_NONE.
        """
    def set_poweron_time(self, tm: PowerOnTime) -> maix._maix.err.Err:
        """
        Set power-on time, The device will power on
        if the power button is held down longer than this time.
        
        Args:
          - tm: The time to be set, you can set it to 128ms, 512ms, 1s, or 2s.
        
        
        Returns: err::Err type, if set success, return err::ERR_NONE.
        """
class ChargerCurrent:
    """
    Members:
    
      CHG_CUR_0MA
    
      CHG_CUR_100MA
    
      CHG_CUR_125MA
    
      CHG_CUR_150MA
    
      CHG_CUR_175MA
    
      CHG_CUR_200MA
    
      CHG_CUR_300MA
    
      CHG_CUR_400MA
    
      CHG_CUR_500MA
    
      CHG_CUR_600MA
    
      CHG_CUR_700MA
    
      CHG_CUR_800MA
    
      CHG_CUR_900MA
    
      CHG_CUR_1000MA
    """
    CHG_CUR_0MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_0MA: 0>
    CHG_CUR_1000MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_1000MA: 16>
    CHG_CUR_100MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_100MA: 4>
    CHG_CUR_125MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_125MA: 5>
    CHG_CUR_150MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_150MA: 6>
    CHG_CUR_175MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_175MA: 7>
    CHG_CUR_200MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_200MA: 8>
    CHG_CUR_300MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_300MA: 9>
    CHG_CUR_400MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_400MA: 10>
    CHG_CUR_500MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_500MA: 11>
    CHG_CUR_600MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_600MA: 12>
    CHG_CUR_700MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_700MA: 13>
    CHG_CUR_800MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_800MA: 14>
    CHG_CUR_900MA: typing.ClassVar[ChargerCurrent]  # value = <ChargerCurrent.CHG_CUR_900MA: 15>
    __members__: typing.ClassVar[dict[str, ChargerCurrent]]  # value = {'CHG_CUR_0MA': <ChargerCurrent.CHG_CUR_0MA: 0>, 'CHG_CUR_100MA': <ChargerCurrent.CHG_CUR_100MA: 4>, 'CHG_CUR_125MA': <ChargerCurrent.CHG_CUR_125MA: 5>, 'CHG_CUR_150MA': <ChargerCurrent.CHG_CUR_150MA: 6>, 'CHG_CUR_175MA': <ChargerCurrent.CHG_CUR_175MA: 7>, 'CHG_CUR_200MA': <ChargerCurrent.CHG_CUR_200MA: 8>, 'CHG_CUR_300MA': <ChargerCurrent.CHG_CUR_300MA: 9>, 'CHG_CUR_400MA': <ChargerCurrent.CHG_CUR_400MA: 10>, 'CHG_CUR_500MA': <ChargerCurrent.CHG_CUR_500MA: 11>, 'CHG_CUR_600MA': <ChargerCurrent.CHG_CUR_600MA: 12>, 'CHG_CUR_700MA': <ChargerCurrent.CHG_CUR_700MA: 13>, 'CHG_CUR_800MA': <ChargerCurrent.CHG_CUR_800MA: 14>, 'CHG_CUR_900MA': <ChargerCurrent.CHG_CUR_900MA: 15>, 'CHG_CUR_1000MA': <ChargerCurrent.CHG_CUR_1000MA: 16>}
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
class ChargerStatus:
    """
    Members:
    
      CHG_TRI_STATE
    
      CHG_PRE_STATE
    
      CHG_CC_STATE
    
      CHG_CV_STATE
    
      CHG_DONE_STATE
    
      CHG_STOP_STATE
    """
    CHG_CC_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_CC_STATE: 2>
    CHG_CV_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_CV_STATE: 3>
    CHG_DONE_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_DONE_STATE: 4>
    CHG_PRE_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_PRE_STATE: 1>
    CHG_STOP_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_STOP_STATE: 5>
    CHG_TRI_STATE: typing.ClassVar[ChargerStatus]  # value = <ChargerStatus.CHG_TRI_STATE: 0>
    __members__: typing.ClassVar[dict[str, ChargerStatus]]  # value = {'CHG_TRI_STATE': <ChargerStatus.CHG_TRI_STATE: 0>, 'CHG_PRE_STATE': <ChargerStatus.CHG_PRE_STATE: 1>, 'CHG_CC_STATE': <ChargerStatus.CHG_CC_STATE: 2>, 'CHG_CV_STATE': <ChargerStatus.CHG_CV_STATE: 3>, 'CHG_DONE_STATE': <ChargerStatus.CHG_DONE_STATE: 4>, 'CHG_STOP_STATE': <ChargerStatus.CHG_STOP_STATE: 5>}
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
class PowerChannel:
    """
    Members:
    
      DCDC1
    
      DCDC2
    
      DCDC3
    
      DCDC4
    
      DCDC5
    
      ALDO1
    
      ALDO2
    
      ALDO3
    
      ALDO4
    
      BLDO1
    
      BLDO2
    
      DLDO1
    
      DLDO2
    
      VBACKUP
    
      CPULDO
    """
    ALDO1: typing.ClassVar[PowerChannel]  # value = <PowerChannel.ALDO1: 5>
    ALDO2: typing.ClassVar[PowerChannel]  # value = <PowerChannel.ALDO2: 6>
    ALDO3: typing.ClassVar[PowerChannel]  # value = <PowerChannel.ALDO3: 7>
    ALDO4: typing.ClassVar[PowerChannel]  # value = <PowerChannel.ALDO4: 8>
    BLDO1: typing.ClassVar[PowerChannel]  # value = <PowerChannel.BLDO1: 9>
    BLDO2: typing.ClassVar[PowerChannel]  # value = <PowerChannel.BLDO2: 10>
    CPULDO: typing.ClassVar[PowerChannel]  # value = <PowerChannel.CPULDO: 14>
    DCDC1: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DCDC1: 0>
    DCDC2: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DCDC2: 1>
    DCDC3: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DCDC3: 2>
    DCDC4: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DCDC4: 3>
    DCDC5: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DCDC5: 4>
    DLDO1: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DLDO1: 11>
    DLDO2: typing.ClassVar[PowerChannel]  # value = <PowerChannel.DLDO2: 12>
    VBACKUP: typing.ClassVar[PowerChannel]  # value = <PowerChannel.VBACKUP: 13>
    __members__: typing.ClassVar[dict[str, PowerChannel]]  # value = {'DCDC1': <PowerChannel.DCDC1: 0>, 'DCDC2': <PowerChannel.DCDC2: 1>, 'DCDC3': <PowerChannel.DCDC3: 2>, 'DCDC4': <PowerChannel.DCDC4: 3>, 'DCDC5': <PowerChannel.DCDC5: 4>, 'ALDO1': <PowerChannel.ALDO1: 5>, 'ALDO2': <PowerChannel.ALDO2: 6>, 'ALDO3': <PowerChannel.ALDO3: 7>, 'ALDO4': <PowerChannel.ALDO4: 8>, 'BLDO1': <PowerChannel.BLDO1: 9>, 'BLDO2': <PowerChannel.BLDO2: 10>, 'DLDO1': <PowerChannel.DLDO1: 11>, 'DLDO2': <PowerChannel.DLDO2: 12>, 'VBACKUP': <PowerChannel.VBACKUP: 13>, 'CPULDO': <PowerChannel.CPULDO: 14>}
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
class PowerOffTime:
    """
    Members:
    
      POWEROFF_4S
    
      POWEROFF_6S
    
      POWEROFF_8S
    
      POWEROFF_10S
    
      POWEROFF_DISABLE
    """
    POWEROFF_10S: typing.ClassVar[PowerOffTime]  # value = <PowerOffTime.POWEROFF_10S: 3>
    POWEROFF_4S: typing.ClassVar[PowerOffTime]  # value = <PowerOffTime.POWEROFF_4S: 0>
    POWEROFF_6S: typing.ClassVar[PowerOffTime]  # value = <PowerOffTime.POWEROFF_6S: 1>
    POWEROFF_8S: typing.ClassVar[PowerOffTime]  # value = <PowerOffTime.POWEROFF_8S: 2>
    POWEROFF_DISABLE: typing.ClassVar[PowerOffTime]  # value = <PowerOffTime.POWEROFF_DISABLE: 65535>
    __members__: typing.ClassVar[dict[str, PowerOffTime]]  # value = {'POWEROFF_4S': <PowerOffTime.POWEROFF_4S: 0>, 'POWEROFF_6S': <PowerOffTime.POWEROFF_6S: 1>, 'POWEROFF_8S': <PowerOffTime.POWEROFF_8S: 2>, 'POWEROFF_10S': <PowerOffTime.POWEROFF_10S: 3>, 'POWEROFF_DISABLE': <PowerOffTime.POWEROFF_DISABLE: 65535>}
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
class PowerOnTime:
    """
    Members:
    
      POWERON_128MS
    
      POWERON_512MS
    
      POWERON_1S
    
      POWERON_2S
    """
    POWERON_128MS: typing.ClassVar[PowerOnTime]  # value = <PowerOnTime.POWERON_128MS: 0>
    POWERON_1S: typing.ClassVar[PowerOnTime]  # value = <PowerOnTime.POWERON_1S: 2>
    POWERON_2S: typing.ClassVar[PowerOnTime]  # value = <PowerOnTime.POWERON_2S: 3>
    POWERON_512MS: typing.ClassVar[PowerOnTime]  # value = <PowerOnTime.POWERON_512MS: 1>
    __members__: typing.ClassVar[dict[str, PowerOnTime]]  # value = {'POWERON_128MS': <PowerOnTime.POWERON_128MS: 0>, 'POWERON_512MS': <PowerOnTime.POWERON_512MS: 1>, 'POWERON_1S': <PowerOnTime.POWERON_1S: 2>, 'POWERON_2S': <PowerOnTime.POWERON_2S: 3>}
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
