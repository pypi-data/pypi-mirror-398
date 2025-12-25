from zepben.protobuf.cim.iec61968.common import Agreement_pb2 as _Agreement_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CustomerAgreement(_message.Message):
    __slots__ = ("agr", "customerMRID", "pricingStructureMRIDs")
    AGR_FIELD_NUMBER: _ClassVar[int]
    CUSTOMERMRID_FIELD_NUMBER: _ClassVar[int]
    PRICINGSTRUCTUREMRIDS_FIELD_NUMBER: _ClassVar[int]
    agr: _Agreement_pb2.Agreement
    customerMRID: str
    pricingStructureMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, agr: _Optional[_Union[_Agreement_pb2.Agreement, _Mapping]] = ..., customerMRID: _Optional[str] = ..., pricingStructureMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
