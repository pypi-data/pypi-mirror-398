from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class BatteryControlMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BATTERY_CONTROL_MODE_UNKNOWN: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_PEAK_SHAVE_DISCHARGE: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_CURRENT_PEAK_SHAVE_DISCHARGE: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_FOLLOWING: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_SUPPORT: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_SCHEDULE: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_PEAK_SHAVE_CHARGE: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_CURRENT_PEAK_SHAVE_CHARGE: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_TIME: _ClassVar[BatteryControlMode]
    BATTERY_CONTROL_MODE_PROFILE: _ClassVar[BatteryControlMode]
BATTERY_CONTROL_MODE_UNKNOWN: BatteryControlMode
BATTERY_CONTROL_MODE_PEAK_SHAVE_DISCHARGE: BatteryControlMode
BATTERY_CONTROL_MODE_CURRENT_PEAK_SHAVE_DISCHARGE: BatteryControlMode
BATTERY_CONTROL_MODE_FOLLOWING: BatteryControlMode
BATTERY_CONTROL_MODE_SUPPORT: BatteryControlMode
BATTERY_CONTROL_MODE_SCHEDULE: BatteryControlMode
BATTERY_CONTROL_MODE_PEAK_SHAVE_CHARGE: BatteryControlMode
BATTERY_CONTROL_MODE_CURRENT_PEAK_SHAVE_CHARGE: BatteryControlMode
BATTERY_CONTROL_MODE_TIME: BatteryControlMode
BATTERY_CONTROL_MODE_PROFILE: BatteryControlMode
