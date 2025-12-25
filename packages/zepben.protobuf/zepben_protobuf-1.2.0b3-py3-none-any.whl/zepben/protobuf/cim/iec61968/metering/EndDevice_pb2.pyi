from zepben.protobuf.cim.iec61968.assets import AssetContainer_pb2 as _AssetContainer_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EndDevice(_message.Message):
    __slots__ = ("ac", "usagePointMRIDs", "customerMRID", "serviceLocationMRID", "endDeviceFunctionMRIDs")
    AC_FIELD_NUMBER: _ClassVar[int]
    USAGEPOINTMRIDS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMERMRID_FIELD_NUMBER: _ClassVar[int]
    SERVICELOCATIONMRID_FIELD_NUMBER: _ClassVar[int]
    ENDDEVICEFUNCTIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    ac: _AssetContainer_pb2.AssetContainer
    usagePointMRIDs: _containers.RepeatedScalarFieldContainer[str]
    customerMRID: str
    serviceLocationMRID: str
    endDeviceFunctionMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ac: _Optional[_Union[_AssetContainer_pb2.AssetContainer, _Mapping]] = ..., usagePointMRIDs: _Optional[_Iterable[str]] = ..., customerMRID: _Optional[str] = ..., serviceLocationMRID: _Optional[str] = ..., endDeviceFunctionMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
