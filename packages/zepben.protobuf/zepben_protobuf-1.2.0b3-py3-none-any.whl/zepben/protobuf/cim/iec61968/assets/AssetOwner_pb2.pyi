from zepben.protobuf.cim.iec61968.assets import AssetOrganisationRole_pb2 as _AssetOrganisationRole_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AssetOwner(_message.Message):
    __slots__ = ("aor",)
    AOR_FIELD_NUMBER: _ClassVar[int]
    aor: _AssetOrganisationRole_pb2.AssetOrganisationRole
    def __init__(self, aor: _Optional[_Union[_AssetOrganisationRole_pb2.AssetOrganisationRole, _Mapping]] = ...) -> None: ...
