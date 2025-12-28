"""
maix.ext_dev.pmu module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['ChargerStatus', 'PMU', 'PowerChannel']
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
class PMU:
    def __init__(self, driver: str = '', i2c_bus: int = -1, addr: int = 52) -> None:
        ...
    def clean_irq(self) -> maix._maix.err.Err:
        """
        Clear interrupt flag.
        
        Returns: err::Err type, if clean success, return err::ERR_NONE.
        """
    def get_bat_charging_cur(self) -> int:
        """
        Get the battery charging current.
        
        Returns: int, return the currently set charging current.
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
    def get_vol(self, channel: PowerChannel) -> int:
        """
        Get the PMU channel voltage.
        You can retrieve the available channel from ext_dev.pmu.PowerChannel.
        
        Returns: err::Err type, if set success, return err::ERR_NONE.
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
    def set_bat_charging_cur(self, current: int) -> maix._maix.err.Err:
        """
        Set the battery charging current.
        
        Args:
          - current: The current to be set.
        
        
        Returns: err::Err type, if set success, return err::ERR_NONE.
        """
    def set_vol(self, channel: PowerChannel, voltage: int) -> maix._maix.err.Err:
        """
        Set the PMU channel voltage.
        You can retrieve the available channel from ext_dev.pmu.PowerChannel.
        
        Args:
          - voltage: The voltage to be set.
        
        
        Returns: int, return the channel voltage.
        """
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
