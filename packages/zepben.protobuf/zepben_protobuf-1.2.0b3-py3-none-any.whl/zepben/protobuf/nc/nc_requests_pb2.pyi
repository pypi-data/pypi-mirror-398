from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IncludedEnergizingContainers(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INCLUDED_ENERGIZING_CONTAINERS_NONE: _ClassVar[IncludedEnergizingContainers]
    INCLUDED_ENERGIZING_CONTAINERS_FEEDERS: _ClassVar[IncludedEnergizingContainers]
    INCLUDED_ENERGIZING_CONTAINERS_SUBSTATIONS: _ClassVar[IncludedEnergizingContainers]

class IncludedEnergizedContainers(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INCLUDED_ENERGIZED_CONTAINERS_NONE: _ClassVar[IncludedEnergizedContainers]
    INCLUDED_ENERGIZED_CONTAINERS_FEEDERS: _ClassVar[IncludedEnergizedContainers]
    INCLUDED_ENERGIZED_CONTAINERS_LV_FEEDERS: _ClassVar[IncludedEnergizedContainers]

class NetworkState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NETWORK_STATE_ALL: _ClassVar[NetworkState]
    NETWORK_STATE_NORMAL: _ClassVar[NetworkState]
    NETWORK_STATE_CURRENT: _ClassVar[NetworkState]
INCLUDED_ENERGIZING_CONTAINERS_NONE: IncludedEnergizingContainers
INCLUDED_ENERGIZING_CONTAINERS_FEEDERS: IncludedEnergizingContainers
INCLUDED_ENERGIZING_CONTAINERS_SUBSTATIONS: IncludedEnergizingContainers
INCLUDED_ENERGIZED_CONTAINERS_NONE: IncludedEnergizedContainers
INCLUDED_ENERGIZED_CONTAINERS_FEEDERS: IncludedEnergizedContainers
INCLUDED_ENERGIZED_CONTAINERS_LV_FEEDERS: IncludedEnergizedContainers
NETWORK_STATE_ALL: NetworkState
NETWORK_STATE_NORMAL: NetworkState
NETWORK_STATE_CURRENT: NetworkState

class GetIdentifiedObjectsRequest(_message.Message):
    __slots__ = ("messageId", "mrids")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRIDS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, messageId: _Optional[int] = ..., mrids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetNetworkHierarchyRequest(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class GetEquipmentForContainersRequest(_message.Message):
    __slots__ = ("messageId", "mrids", "includeEnergizingContainers", "includeEnergizedContainers", "networkState")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRIDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDEENERGIZINGCONTAINERS_FIELD_NUMBER: _ClassVar[int]
    INCLUDEENERGIZEDCONTAINERS_FIELD_NUMBER: _ClassVar[int]
    NETWORKSTATE_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrids: _containers.RepeatedScalarFieldContainer[str]
    includeEnergizingContainers: IncludedEnergizingContainers
    includeEnergizedContainers: IncludedEnergizedContainers
    networkState: NetworkState
    def __init__(self, messageId: _Optional[int] = ..., mrids: _Optional[_Iterable[str]] = ..., includeEnergizingContainers: _Optional[_Union[IncludedEnergizingContainers, str]] = ..., includeEnergizedContainers: _Optional[_Union[IncludedEnergizedContainers, str]] = ..., networkState: _Optional[_Union[NetworkState, str]] = ...) -> None: ...

class GetEquipmentForRestrictionRequest(_message.Message):
    __slots__ = ("messageId", "mrid")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrid: str
    def __init__(self, messageId: _Optional[int] = ..., mrid: _Optional[str] = ...) -> None: ...

class GetTerminalsForNodeRequest(_message.Message):
    __slots__ = ("messageId", "mrid")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrid: str
    def __init__(self, messageId: _Optional[int] = ..., mrid: _Optional[str] = ...) -> None: ...
