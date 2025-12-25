from zepben.protobuf.nc import nc_data_pb2 as _nc_data_pb2
from zepben.protobuf.cim.extensions.iec61970.base.feeder import Loop_pb2 as _Loop_pb2
from zepben.protobuf.cim.iec61970.base.core import Feeder_pb2 as _Feeder_pb2
from zepben.protobuf.cim.iec61970.base.core import GeographicalRegion_pb2 as _GeographicalRegion_pb2
from zepben.protobuf.cim.iec61970.base.core import SubGeographicalRegion_pb2 as _SubGeographicalRegion_pb2
from zepben.protobuf.cim.iec61970.base.core import Substation_pb2 as _Substation_pb2
from zepben.protobuf.cim.iec61970.base.core import Terminal_pb2 as _Terminal_pb2
from zepben.protobuf.cim.iec61970.infiec61970.feeder import Circuit_pb2 as _Circuit_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetNetworkHierarchyResponse(_message.Message):
    __slots__ = ("messageId", "geographicalRegions", "subGeographicalRegions", "substations", "feeders", "circuits", "loops")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    GEOGRAPHICALREGIONS_FIELD_NUMBER: _ClassVar[int]
    SUBGEOGRAPHICALREGIONS_FIELD_NUMBER: _ClassVar[int]
    SUBSTATIONS_FIELD_NUMBER: _ClassVar[int]
    FEEDERS_FIELD_NUMBER: _ClassVar[int]
    CIRCUITS_FIELD_NUMBER: _ClassVar[int]
    LOOPS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    geographicalRegions: _containers.RepeatedCompositeFieldContainer[_GeographicalRegion_pb2.GeographicalRegion]
    subGeographicalRegions: _containers.RepeatedCompositeFieldContainer[_SubGeographicalRegion_pb2.SubGeographicalRegion]
    substations: _containers.RepeatedCompositeFieldContainer[_Substation_pb2.Substation]
    feeders: _containers.RepeatedCompositeFieldContainer[_Feeder_pb2.Feeder]
    circuits: _containers.RepeatedCompositeFieldContainer[_Circuit_pb2.Circuit]
    loops: _containers.RepeatedCompositeFieldContainer[_Loop_pb2.Loop]
    def __init__(self, messageId: _Optional[int] = ..., geographicalRegions: _Optional[_Iterable[_Union[_GeographicalRegion_pb2.GeographicalRegion, _Mapping]]] = ..., subGeographicalRegions: _Optional[_Iterable[_Union[_SubGeographicalRegion_pb2.SubGeographicalRegion, _Mapping]]] = ..., substations: _Optional[_Iterable[_Union[_Substation_pb2.Substation, _Mapping]]] = ..., feeders: _Optional[_Iterable[_Union[_Feeder_pb2.Feeder, _Mapping]]] = ..., circuits: _Optional[_Iterable[_Union[_Circuit_pb2.Circuit, _Mapping]]] = ..., loops: _Optional[_Iterable[_Union[_Loop_pb2.Loop, _Mapping]]] = ...) -> None: ...

class GetIdentifiedObjectsResponse(_message.Message):
    __slots__ = ("messageId", "identifiedObjects")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    identifiedObjects: _containers.RepeatedCompositeFieldContainer[_nc_data_pb2.NetworkIdentifiedObject]
    def __init__(self, messageId: _Optional[int] = ..., identifiedObjects: _Optional[_Iterable[_Union[_nc_data_pb2.NetworkIdentifiedObject, _Mapping]]] = ...) -> None: ...

class GetEquipmentForContainersResponse(_message.Message):
    __slots__ = ("messageId", "identifiedObjects")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    identifiedObjects: _containers.RepeatedCompositeFieldContainer[_nc_data_pb2.NetworkIdentifiedObject]
    def __init__(self, messageId: _Optional[int] = ..., identifiedObjects: _Optional[_Iterable[_Union[_nc_data_pb2.NetworkIdentifiedObject, _Mapping]]] = ...) -> None: ...

class GetEquipmentForRestrictionResponse(_message.Message):
    __slots__ = ("messageId", "identifiedObjects")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    identifiedObjects: _containers.RepeatedCompositeFieldContainer[_nc_data_pb2.NetworkIdentifiedObject]
    def __init__(self, messageId: _Optional[int] = ..., identifiedObjects: _Optional[_Iterable[_Union[_nc_data_pb2.NetworkIdentifiedObject, _Mapping]]] = ...) -> None: ...

class GetTerminalsForNodeResponse(_message.Message):
    __slots__ = ("messageId", "terminal")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    terminal: _Terminal_pb2.Terminal
    def __init__(self, messageId: _Optional[int] = ..., terminal: _Optional[_Union[_Terminal_pb2.Terminal, _Mapping]] = ...) -> None: ...
