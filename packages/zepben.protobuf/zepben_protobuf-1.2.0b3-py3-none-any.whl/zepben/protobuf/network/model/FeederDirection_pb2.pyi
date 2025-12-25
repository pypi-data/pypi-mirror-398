from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class FeederDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FEEDER_DIRECTION_NONE: _ClassVar[FeederDirection]
    FEEDER_DIRECTION_UPSTREAM: _ClassVar[FeederDirection]
    FEEDER_DIRECTION_DOWNSTREAM: _ClassVar[FeederDirection]
    FEEDER_DIRECTION_BOTH: _ClassVar[FeederDirection]
    FEEDER_DIRECTION_CONNECTOR: _ClassVar[FeederDirection]
FEEDER_DIRECTION_NONE: FeederDirection
FEEDER_DIRECTION_UPSTREAM: FeederDirection
FEEDER_DIRECTION_DOWNSTREAM: FeederDirection
FEEDER_DIRECTION_BOTH: FeederDirection
FEEDER_DIRECTION_CONNECTOR: FeederDirection
