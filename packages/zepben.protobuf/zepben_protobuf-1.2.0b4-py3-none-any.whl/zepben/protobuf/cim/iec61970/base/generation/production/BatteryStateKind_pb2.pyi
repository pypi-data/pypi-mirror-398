from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class BatteryStateKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BATTERY_STATE_KIND_UNKNOWN: _ClassVar[BatteryStateKind]
    BATTERY_STATE_KIND_DISCHARGING: _ClassVar[BatteryStateKind]
    BATTERY_STATE_KIND_FULL: _ClassVar[BatteryStateKind]
    BATTERY_STATE_KIND_WAITING: _ClassVar[BatteryStateKind]
    BATTERY_STATE_KIND_CHARGING: _ClassVar[BatteryStateKind]
    BATTERY_STATE_KIND_EMPTY: _ClassVar[BatteryStateKind]
BATTERY_STATE_KIND_UNKNOWN: BatteryStateKind
BATTERY_STATE_KIND_DISCHARGING: BatteryStateKind
BATTERY_STATE_KIND_FULL: BatteryStateKind
BATTERY_STATE_KIND_WAITING: BatteryStateKind
BATTERY_STATE_KIND_CHARGING: BatteryStateKind
BATTERY_STATE_KIND_EMPTY: BatteryStateKind
