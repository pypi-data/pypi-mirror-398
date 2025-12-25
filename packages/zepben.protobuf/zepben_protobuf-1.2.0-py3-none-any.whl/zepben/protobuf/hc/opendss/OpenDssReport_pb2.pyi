from zepben.protobuf.hc.opendss import EnergyMeter_pb2 as _EnergyMeter_pb2
from zepben.protobuf.hc.opendss import Diagnostics_pb2 as _Diagnostics_pb2
from zepben.protobuf.hc.opendss import SamplePointReport_pb2 as _SamplePointReport_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OpenDssReport(_message.Message):
    __slots__ = ("di", "phv", "ov", "vr", "sr", "el", "tr", "lr", "ibr", "le", "losses", "nm", "kvm", "failure", "spr")
    DI_FIELD_NUMBER: _ClassVar[int]
    PHV_FIELD_NUMBER: _ClassVar[int]
    OV_FIELD_NUMBER: _ClassVar[int]
    VR_FIELD_NUMBER: _ClassVar[int]
    SR_FIELD_NUMBER: _ClassVar[int]
    EL_FIELD_NUMBER: _ClassVar[int]
    TR_FIELD_NUMBER: _ClassVar[int]
    LR_FIELD_NUMBER: _ClassVar[int]
    IBR_FIELD_NUMBER: _ClassVar[int]
    LE_FIELD_NUMBER: _ClassVar[int]
    LOSSES_FIELD_NUMBER: _ClassVar[int]
    NM_FIELD_NUMBER: _ClassVar[int]
    KVM_FIELD_NUMBER: _ClassVar[int]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    SPR_FIELD_NUMBER: _ClassVar[int]
    di: _EnergyMeter_pb2.DemandIntervalReport
    phv: _EnergyMeter_pb2.PhaseVoltageReport
    ov: _EnergyMeter_pb2.OverloadReport
    vr: _EnergyMeter_pb2.VoltageReport
    sr: _Diagnostics_pb2.SummaryReport
    el: _Diagnostics_pb2.EventLog
    tr: _Diagnostics_pb2.TapsReport
    lr: _Diagnostics_pb2.LoopReport
    ibr: _Diagnostics_pb2.IsolatedBusesReport
    le: _Diagnostics_pb2.LossesEntry
    losses: _Diagnostics_pb2.LossesTotals
    nm: _Diagnostics_pb2.NodeMismatch
    kvm: _Diagnostics_pb2.KVBaseMismatch
    failure: bool
    spr: _SamplePointReport_pb2.SamplePointReport
    def __init__(self, di: _Optional[_Union[_EnergyMeter_pb2.DemandIntervalReport, _Mapping]] = ..., phv: _Optional[_Union[_EnergyMeter_pb2.PhaseVoltageReport, _Mapping]] = ..., ov: _Optional[_Union[_EnergyMeter_pb2.OverloadReport, _Mapping]] = ..., vr: _Optional[_Union[_EnergyMeter_pb2.VoltageReport, _Mapping]] = ..., sr: _Optional[_Union[_Diagnostics_pb2.SummaryReport, _Mapping]] = ..., el: _Optional[_Union[_Diagnostics_pb2.EventLog, _Mapping]] = ..., tr: _Optional[_Union[_Diagnostics_pb2.TapsReport, _Mapping]] = ..., lr: _Optional[_Union[_Diagnostics_pb2.LoopReport, _Mapping]] = ..., ibr: _Optional[_Union[_Diagnostics_pb2.IsolatedBusesReport, _Mapping]] = ..., le: _Optional[_Union[_Diagnostics_pb2.LossesEntry, _Mapping]] = ..., losses: _Optional[_Union[_Diagnostics_pb2.LossesTotals, _Mapping]] = ..., nm: _Optional[_Union[_Diagnostics_pb2.NodeMismatch, _Mapping]] = ..., kvm: _Optional[_Union[_Diagnostics_pb2.KVBaseMismatch, _Mapping]] = ..., failure: bool = ..., spr: _Optional[_Union[_SamplePointReport_pb2.SamplePointReport, _Mapping]] = ...) -> None: ...

class OpenDssReportBatch(_message.Message):
    __slots__ = ("reports",)
    REPORTS_FIELD_NUMBER: _ClassVar[int]
    reports: _containers.RepeatedCompositeFieldContainer[OpenDssReport]
    def __init__(self, reports: _Optional[_Iterable[_Union[OpenDssReport, _Mapping]]] = ...) -> None: ...
