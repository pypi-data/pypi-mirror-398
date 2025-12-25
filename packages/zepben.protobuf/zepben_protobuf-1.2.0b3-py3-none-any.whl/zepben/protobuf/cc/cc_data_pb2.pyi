from google.protobuf import any_pb2 as _any_pb2
from zepben.protobuf.cim.iec61968.common import Organisation_pb2 as _Organisation_pb2
from zepben.protobuf.cim.iec61968.customers import Customer_pb2 as _Customer_pb2
from zepben.protobuf.cim.iec61968.customers import CustomerAgreement_pb2 as _CustomerAgreement_pb2
from zepben.protobuf.cim.iec61968.customers import PricingStructure_pb2 as _PricingStructure_pb2
from zepben.protobuf.cim.iec61968.customers import Tariff_pb2 as _Tariff_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CustomerIdentifiedObject(_message.Message):
    __slots__ = ("organisation", "customer", "customerAgreement", "pricingStructure", "tariff", "other")
    ORGANISATION_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_FIELD_NUMBER: _ClassVar[int]
    CUSTOMERAGREEMENT_FIELD_NUMBER: _ClassVar[int]
    PRICINGSTRUCTURE_FIELD_NUMBER: _ClassVar[int]
    TARIFF_FIELD_NUMBER: _ClassVar[int]
    OTHER_FIELD_NUMBER: _ClassVar[int]
    organisation: _Organisation_pb2.Organisation
    customer: _Customer_pb2.Customer
    customerAgreement: _CustomerAgreement_pb2.CustomerAgreement
    pricingStructure: _PricingStructure_pb2.PricingStructure
    tariff: _Tariff_pb2.Tariff
    other: _any_pb2.Any
    def __init__(self, organisation: _Optional[_Union[_Organisation_pb2.Organisation, _Mapping]] = ..., customer: _Optional[_Union[_Customer_pb2.Customer, _Mapping]] = ..., customerAgreement: _Optional[_Union[_CustomerAgreement_pb2.CustomerAgreement, _Mapping]] = ..., pricingStructure: _Optional[_Union[_PricingStructure_pb2.PricingStructure, _Mapping]] = ..., tariff: _Optional[_Union[_Tariff_pb2.Tariff, _Mapping]] = ..., other: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
