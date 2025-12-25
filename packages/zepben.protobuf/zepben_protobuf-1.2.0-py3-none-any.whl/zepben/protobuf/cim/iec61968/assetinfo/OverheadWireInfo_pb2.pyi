from zepben.protobuf.cim.iec61968.assetinfo import WireInfo_pb2 as _WireInfo_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OverheadWireInfo(_message.Message):
    __slots__ = ("wi",)
    WI_FIELD_NUMBER: _ClassVar[int]
    wi: _WireInfo_pb2.WireInfo
    def __init__(self, wi: _Optional[_Union[_WireInfo_pb2.WireInfo, _Mapping]] = ...) -> None: ...
