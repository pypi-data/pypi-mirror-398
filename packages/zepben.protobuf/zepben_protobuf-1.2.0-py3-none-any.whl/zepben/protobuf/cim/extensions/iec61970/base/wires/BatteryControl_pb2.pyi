from zepben.protobuf.cim.iec61970.base.wires import RegulatingControl_pb2 as _RegulatingControl_pb2
from zepben.protobuf.cim.extensions.iec61970.base.wires import BatteryControlMode_pb2 as _BatteryControlMode_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BatteryControl(_message.Message):
    __slots__ = ("rc", "chargingRateNull", "chargingRateSet", "dischargingRateNull", "dischargingRateSet", "reservePercentNull", "reservePercentSet", "controlMode")
    RC_FIELD_NUMBER: _ClassVar[int]
    CHARGINGRATENULL_FIELD_NUMBER: _ClassVar[int]
    CHARGINGRATESET_FIELD_NUMBER: _ClassVar[int]
    DISCHARGINGRATENULL_FIELD_NUMBER: _ClassVar[int]
    DISCHARGINGRATESET_FIELD_NUMBER: _ClassVar[int]
    RESERVEPERCENTNULL_FIELD_NUMBER: _ClassVar[int]
    RESERVEPERCENTSET_FIELD_NUMBER: _ClassVar[int]
    CONTROLMODE_FIELD_NUMBER: _ClassVar[int]
    rc: _RegulatingControl_pb2.RegulatingControl
    chargingRateNull: _struct_pb2.NullValue
    chargingRateSet: float
    dischargingRateNull: _struct_pb2.NullValue
    dischargingRateSet: float
    reservePercentNull: _struct_pb2.NullValue
    reservePercentSet: float
    controlMode: _BatteryControlMode_pb2.BatteryControlMode
    def __init__(self, rc: _Optional[_Union[_RegulatingControl_pb2.RegulatingControl, _Mapping]] = ..., chargingRateNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., chargingRateSet: _Optional[float] = ..., dischargingRateNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., dischargingRateSet: _Optional[float] = ..., reservePercentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., reservePercentSet: _Optional[float] = ..., controlMode: _Optional[_Union[_BatteryControlMode_pb2.BatteryControlMode, str]] = ...) -> None: ...
