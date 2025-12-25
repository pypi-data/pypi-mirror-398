from google.protobuf import any_pb2 as _any_pb2
from zepben.protobuf.cim.extensions.iec61968.assetinfo import RelayInfo_pb2 as _RelayInfo_pb2
from zepben.protobuf.cim.extensions.iec61968.metering import PanDemandResponseFunction_pb2 as _PanDemandResponseFunction_pb2
from zepben.protobuf.cim.extensions.iec61970.base.core import Site_pb2 as _Site_pb2
from zepben.protobuf.cim.extensions.iec61970.base.feeder import Loop_pb2 as _Loop_pb2
from zepben.protobuf.cim.extensions.iec61970.base.feeder import LvFeeder_pb2 as _LvFeeder_pb2
from zepben.protobuf.cim.extensions.iec61970.base.generation.production import EvChargingUnit_pb2 as _EvChargingUnit_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import DirectionalCurrentRelay_pb2 as _DirectionalCurrentRelay_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import DistanceRelay_pb2 as _DistanceRelay_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelayScheme_pb2 as _ProtectionRelayScheme_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelaySystem_pb2 as _ProtectionRelaySystem_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import VoltageRelay_pb2 as _VoltageRelay_pb2
from zepben.protobuf.cim.extensions.iec61970.base.wires import BatteryControl_pb2 as _BatteryControl_pb2
from zepben.protobuf.cim.iec61968.assetinfo import CableInfo_pb2 as _CableInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import NoLoadTest_pb2 as _NoLoadTest_pb2
from zepben.protobuf.cim.iec61968.assetinfo import OpenCircuitTest_pb2 as _OpenCircuitTest_pb2
from zepben.protobuf.cim.iec61968.assetinfo import OverheadWireInfo_pb2 as _OverheadWireInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import PowerTransformerInfo_pb2 as _PowerTransformerInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import ShortCircuitTest_pb2 as _ShortCircuitTest_pb2
from zepben.protobuf.cim.iec61968.assetinfo import ShuntCompensatorInfo_pb2 as _ShuntCompensatorInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import SwitchInfo_pb2 as _SwitchInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import TransformerEndInfo_pb2 as _TransformerEndInfo_pb2
from zepben.protobuf.cim.iec61968.assetinfo import TransformerTankInfo_pb2 as _TransformerTankInfo_pb2
from zepben.protobuf.cim.iec61968.assets import AssetOwner_pb2 as _AssetOwner_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassets import Pole_pb2 as _Pole_pb2
from zepben.protobuf.cim.iec61968.assets import Streetlight_pb2 as _Streetlight_pb2
from zepben.protobuf.cim.iec61968.common import Location_pb2 as _Location_pb2
from zepben.protobuf.cim.iec61968.common import Organisation_pb2 as _Organisation_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassetinfo import CurrentTransformerInfo_pb2 as _CurrentTransformerInfo_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassetinfo import PotentialTransformerInfo_pb2 as _PotentialTransformerInfo_pb2
from zepben.protobuf.cim.iec61968.metering import Meter_pb2 as _Meter_pb2
from zepben.protobuf.cim.iec61968.metering import UsagePoint_pb2 as _UsagePoint_pb2
from zepben.protobuf.cim.iec61968.operations import OperationalRestriction_pb2 as _OperationalRestriction_pb2
from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import CurrentTransformer_pb2 as _CurrentTransformer_pb2
from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import FaultIndicator_pb2 as _FaultIndicator_pb2
from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import PotentialTransformer_pb2 as _PotentialTransformer_pb2
from zepben.protobuf.cim.iec61970.base.core import BaseVoltage_pb2 as _BaseVoltage_pb2
from zepben.protobuf.cim.iec61970.base.core import ConnectivityNode_pb2 as _ConnectivityNode_pb2
from zepben.protobuf.cim.iec61970.base.core import Feeder_pb2 as _Feeder_pb2
from zepben.protobuf.cim.iec61970.base.core import GeographicalRegion_pb2 as _GeographicalRegion_pb2
from zepben.protobuf.cim.iec61970.base.core import SubGeographicalRegion_pb2 as _SubGeographicalRegion_pb2
from zepben.protobuf.cim.iec61970.base.core import Substation_pb2 as _Substation_pb2
from zepben.protobuf.cim.iec61970.base.core import Terminal_pb2 as _Terminal_pb2
from zepben.protobuf.cim.iec61970.base.equivalents import EquivalentBranch_pb2 as _EquivalentBranch_pb2
from zepben.protobuf.cim.iec61970.base.generation.production import BatteryUnit_pb2 as _BatteryUnit_pb2
from zepben.protobuf.cim.iec61970.base.generation.production import PhotoVoltaicUnit_pb2 as _PhotoVoltaicUnit_pb2
from zepben.protobuf.cim.iec61970.base.generation.production import PowerElectronicsWindUnit_pb2 as _PowerElectronicsWindUnit_pb2
from zepben.protobuf.cim.iec61970.base.protection import CurrentRelay_pb2 as _CurrentRelay_pb2
from zepben.protobuf.cim.iec61970.base.meas import Accumulator_pb2 as _Accumulator_pb2
from zepben.protobuf.cim.iec61970.base.meas import Analog_pb2 as _Analog_pb2
from zepben.protobuf.cim.iec61970.base.meas import Control_pb2 as _Control_pb2
from zepben.protobuf.cim.iec61970.base.meas import Discrete_pb2 as _Discrete_pb2
from zepben.protobuf.cim.iec61970.base.scada import RemoteControl_pb2 as _RemoteControl_pb2
from zepben.protobuf.cim.iec61970.base.scada import RemoteSource_pb2 as _RemoteSource_pb2
from zepben.protobuf.cim.iec61970.base.wires import AcLineSegment_pb2 as _AcLineSegment_pb2
from zepben.protobuf.cim.iec61970.base.wires import Breaker_pb2 as _Breaker_pb2
from zepben.protobuf.cim.iec61970.base.wires import BusbarSection_pb2 as _BusbarSection_pb2
from zepben.protobuf.cim.iec61970.base.wires import Cut_pb2 as _Cut_pb2
from zepben.protobuf.cim.iec61970.base.wires import Clamp_pb2 as _Clamp_pb2
from zepben.protobuf.cim.iec61970.base.wires import Disconnector_pb2 as _Disconnector_pb2
from zepben.protobuf.cim.iec61970.base.wires import EnergyConsumer_pb2 as _EnergyConsumer_pb2
from zepben.protobuf.cim.iec61970.base.wires import EnergyConsumerPhase_pb2 as _EnergyConsumerPhase_pb2
from zepben.protobuf.cim.iec61970.base.wires import EnergySource_pb2 as _EnergySource_pb2
from zepben.protobuf.cim.iec61970.base.wires import EnergySourcePhase_pb2 as _EnergySourcePhase_pb2
from zepben.protobuf.cim.iec61970.base.wires import Fuse_pb2 as _Fuse_pb2
from zepben.protobuf.cim.iec61970.base.wires import Ground_pb2 as _Ground_pb2
from zepben.protobuf.cim.iec61970.base.wires import GroundDisconnector_pb2 as _GroundDisconnector_pb2
from zepben.protobuf.cim.iec61970.base.wires import GroundingImpedance_pb2 as _GroundingImpedance_pb2
from zepben.protobuf.cim.iec61970.base.wires import Jumper_pb2 as _Jumper_pb2
from zepben.protobuf.cim.iec61970.base.wires import Junction_pb2 as _Junction_pb2
from zepben.protobuf.cim.iec61970.base.wires import LinearShuntCompensator_pb2 as _LinearShuntCompensator_pb2
from zepben.protobuf.cim.iec61970.base.wires import LoadBreakSwitch_pb2 as _LoadBreakSwitch_pb2
from zepben.protobuf.cim.iec61970.base.wires import PerLengthPhaseImpedance_pb2 as _PerLengthPhaseImpedance_pb2
from zepben.protobuf.cim.iec61970.base.wires import PerLengthSequenceImpedance_pb2 as _PerLengthSequenceImpedance_pb2
from zepben.protobuf.cim.iec61970.base.wires import PetersenCoil_pb2 as _PetersenCoil_pb2
from zepben.protobuf.cim.iec61970.base.wires import PowerElectronicsConnection_pb2 as _PowerElectronicsConnection_pb2
from zepben.protobuf.cim.iec61970.base.wires import PowerElectronicsConnectionPhase_pb2 as _PowerElectronicsConnectionPhase_pb2
from zepben.protobuf.cim.iec61970.base.wires import PowerTransformer_pb2 as _PowerTransformer_pb2
from zepben.protobuf.cim.iec61970.base.wires import PowerTransformerEnd_pb2 as _PowerTransformerEnd_pb2
from zepben.protobuf.cim.iec61970.base.wires import RatioTapChanger_pb2 as _RatioTapChanger_pb2
from zepben.protobuf.cim.iec61970.base.wires import ReactiveCapabilityCurve_pb2 as _ReactiveCapabilityCurve_pb2
from zepben.protobuf.cim.iec61970.base.wires import Recloser_pb2 as _Recloser_pb2
from zepben.protobuf.cim.iec61970.base.wires import SeriesCompensator_pb2 as _SeriesCompensator_pb2
from zepben.protobuf.cim.iec61970.base.wires import StaticVarCompensator_pb2 as _StaticVarCompensator_pb2
from zepben.protobuf.cim.iec61970.base.wires import SynchronousMachine_pb2 as _SynchronousMachine_pb2
from zepben.protobuf.cim.iec61970.base.wires import TapChangerControl_pb2 as _TapChangerControl_pb2
from zepben.protobuf.cim.iec61970.base.wires import TransformerStarImpedance_pb2 as _TransformerStarImpedance_pb2
from zepben.protobuf.cim.iec61970.infiec61970.feeder import Circuit_pb2 as _Circuit_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NetworkIdentifiedObject(_message.Message):
    __slots__ = ("cableInfo", "overheadWireInfo", "assetOwner", "organisation", "location", "meter", "usagePoint", "operationalRestriction", "faultIndicator", "baseVoltage", "connectivityNode", "feeder", "geographicalRegion", "site", "subGeographicalRegion", "substation", "terminal", "acLineSegment", "breaker", "disconnector", "energyConsumer", "energyConsumerPhase", "energySource", "energySourcePhase", "fuse", "jumper", "junction", "linearShuntCompensator", "perLengthSequenceImpedance", "powerTransformer", "powerTransformerEnd", "ratioTapChanger", "recloser", "circuit", "loop", "pole", "streetlight", "accumulator", "analog", "discrete", "control", "remoteControl", "remoteSource", "powerTransformerInfo", "powerElectronicsConnection", "powerElectronicsConnectionPhase", "batteryUnit", "photoVoltaicUnit", "powerElectronicsWindUnit", "busbarSection", "loadBreakSwitch", "transformerStarImpedance", "transformerEndInfo", "transformerTankInfo", "noLoadTest", "openCircuitTest", "shortCircuitTest", "equivalentBranch", "shuntCompensatorInfo", "lvFeeder", "currentTransformer", "potentialTransformer", "currentTransformerInfo", "potentialTransformerInfo", "switchInfo", "relayInfo", "currentRelay", "tapChangerControl", "evChargingUnit", "seriesCompensator", "ground", "groundDisconnector", "protectionRelayScheme", "protectionRelaySystem", "voltageRelay", "distanceRelay", "synchronousMachine", "reactiveCapabilityCurve", "groundingImpedance", "petersenCoil", "staticVarCompensator", "panDemandResponseFunction", "batteryControl", "perLengthPhaseImpedance", "cut", "clamp", "directionalCurrentRelay", "other")
    CABLEINFO_FIELD_NUMBER: _ClassVar[int]
    OVERHEADWIREINFO_FIELD_NUMBER: _ClassVar[int]
    ASSETOWNER_FIELD_NUMBER: _ClassVar[int]
    ORGANISATION_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    METER_FIELD_NUMBER: _ClassVar[int]
    USAGEPOINT_FIELD_NUMBER: _ClassVar[int]
    OPERATIONALRESTRICTION_FIELD_NUMBER: _ClassVar[int]
    FAULTINDICATOR_FIELD_NUMBER: _ClassVar[int]
    BASEVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    CONNECTIVITYNODE_FIELD_NUMBER: _ClassVar[int]
    FEEDER_FIELD_NUMBER: _ClassVar[int]
    GEOGRAPHICALREGION_FIELD_NUMBER: _ClassVar[int]
    SITE_FIELD_NUMBER: _ClassVar[int]
    SUBGEOGRAPHICALREGION_FIELD_NUMBER: _ClassVar[int]
    SUBSTATION_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    ACLINESEGMENT_FIELD_NUMBER: _ClassVar[int]
    BREAKER_FIELD_NUMBER: _ClassVar[int]
    DISCONNECTOR_FIELD_NUMBER: _ClassVar[int]
    ENERGYCONSUMER_FIELD_NUMBER: _ClassVar[int]
    ENERGYCONSUMERPHASE_FIELD_NUMBER: _ClassVar[int]
    ENERGYSOURCE_FIELD_NUMBER: _ClassVar[int]
    ENERGYSOURCEPHASE_FIELD_NUMBER: _ClassVar[int]
    FUSE_FIELD_NUMBER: _ClassVar[int]
    JUMPER_FIELD_NUMBER: _ClassVar[int]
    JUNCTION_FIELD_NUMBER: _ClassVar[int]
    LINEARSHUNTCOMPENSATOR_FIELD_NUMBER: _ClassVar[int]
    PERLENGTHSEQUENCEIMPEDANCE_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMER_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMEREND_FIELD_NUMBER: _ClassVar[int]
    RATIOTAPCHANGER_FIELD_NUMBER: _ClassVar[int]
    RECLOSER_FIELD_NUMBER: _ClassVar[int]
    CIRCUIT_FIELD_NUMBER: _ClassVar[int]
    LOOP_FIELD_NUMBER: _ClassVar[int]
    POLE_FIELD_NUMBER: _ClassVar[int]
    STREETLIGHT_FIELD_NUMBER: _ClassVar[int]
    ACCUMULATOR_FIELD_NUMBER: _ClassVar[int]
    ANALOG_FIELD_NUMBER: _ClassVar[int]
    DISCRETE_FIELD_NUMBER: _ClassVar[int]
    CONTROL_FIELD_NUMBER: _ClassVar[int]
    REMOTECONTROL_FIELD_NUMBER: _ClassVar[int]
    REMOTESOURCE_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMERINFO_FIELD_NUMBER: _ClassVar[int]
    POWERELECTRONICSCONNECTION_FIELD_NUMBER: _ClassVar[int]
    POWERELECTRONICSCONNECTIONPHASE_FIELD_NUMBER: _ClassVar[int]
    BATTERYUNIT_FIELD_NUMBER: _ClassVar[int]
    PHOTOVOLTAICUNIT_FIELD_NUMBER: _ClassVar[int]
    POWERELECTRONICSWINDUNIT_FIELD_NUMBER: _ClassVar[int]
    BUSBARSECTION_FIELD_NUMBER: _ClassVar[int]
    LOADBREAKSWITCH_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERSTARIMPEDANCE_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERENDINFO_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERTANKINFO_FIELD_NUMBER: _ClassVar[int]
    NOLOADTEST_FIELD_NUMBER: _ClassVar[int]
    OPENCIRCUITTEST_FIELD_NUMBER: _ClassVar[int]
    SHORTCIRCUITTEST_FIELD_NUMBER: _ClassVar[int]
    EQUIVALENTBRANCH_FIELD_NUMBER: _ClassVar[int]
    SHUNTCOMPENSATORINFO_FIELD_NUMBER: _ClassVar[int]
    LVFEEDER_FIELD_NUMBER: _ClassVar[int]
    CURRENTTRANSFORMER_FIELD_NUMBER: _ClassVar[int]
    POTENTIALTRANSFORMER_FIELD_NUMBER: _ClassVar[int]
    CURRENTTRANSFORMERINFO_FIELD_NUMBER: _ClassVar[int]
    POTENTIALTRANSFORMERINFO_FIELD_NUMBER: _ClassVar[int]
    SWITCHINFO_FIELD_NUMBER: _ClassVar[int]
    RELAYINFO_FIELD_NUMBER: _ClassVar[int]
    CURRENTRELAY_FIELD_NUMBER: _ClassVar[int]
    TAPCHANGERCONTROL_FIELD_NUMBER: _ClassVar[int]
    EVCHARGINGUNIT_FIELD_NUMBER: _ClassVar[int]
    SERIESCOMPENSATOR_FIELD_NUMBER: _ClassVar[int]
    GROUND_FIELD_NUMBER: _ClassVar[int]
    GROUNDDISCONNECTOR_FIELD_NUMBER: _ClassVar[int]
    PROTECTIONRELAYSCHEME_FIELD_NUMBER: _ClassVar[int]
    PROTECTIONRELAYSYSTEM_FIELD_NUMBER: _ClassVar[int]
    VOLTAGERELAY_FIELD_NUMBER: _ClassVar[int]
    DISTANCERELAY_FIELD_NUMBER: _ClassVar[int]
    SYNCHRONOUSMACHINE_FIELD_NUMBER: _ClassVar[int]
    REACTIVECAPABILITYCURVE_FIELD_NUMBER: _ClassVar[int]
    GROUNDINGIMPEDANCE_FIELD_NUMBER: _ClassVar[int]
    PETERSENCOIL_FIELD_NUMBER: _ClassVar[int]
    STATICVARCOMPENSATOR_FIELD_NUMBER: _ClassVar[int]
    PANDEMANDRESPONSEFUNCTION_FIELD_NUMBER: _ClassVar[int]
    BATTERYCONTROL_FIELD_NUMBER: _ClassVar[int]
    PERLENGTHPHASEIMPEDANCE_FIELD_NUMBER: _ClassVar[int]
    CUT_FIELD_NUMBER: _ClassVar[int]
    CLAMP_FIELD_NUMBER: _ClassVar[int]
    DIRECTIONALCURRENTRELAY_FIELD_NUMBER: _ClassVar[int]
    OTHER_FIELD_NUMBER: _ClassVar[int]
    cableInfo: _CableInfo_pb2.CableInfo
    overheadWireInfo: _OverheadWireInfo_pb2.OverheadWireInfo
    assetOwner: _AssetOwner_pb2.AssetOwner
    organisation: _Organisation_pb2.Organisation
    location: _Location_pb2.Location
    meter: _Meter_pb2.Meter
    usagePoint: _UsagePoint_pb2.UsagePoint
    operationalRestriction: _OperationalRestriction_pb2.OperationalRestriction
    faultIndicator: _FaultIndicator_pb2.FaultIndicator
    baseVoltage: _BaseVoltage_pb2.BaseVoltage
    connectivityNode: _ConnectivityNode_pb2.ConnectivityNode
    feeder: _Feeder_pb2.Feeder
    geographicalRegion: _GeographicalRegion_pb2.GeographicalRegion
    site: _Site_pb2.Site
    subGeographicalRegion: _SubGeographicalRegion_pb2.SubGeographicalRegion
    substation: _Substation_pb2.Substation
    terminal: _Terminal_pb2.Terminal
    acLineSegment: _AcLineSegment_pb2.AcLineSegment
    breaker: _Breaker_pb2.Breaker
    disconnector: _Disconnector_pb2.Disconnector
    energyConsumer: _EnergyConsumer_pb2.EnergyConsumer
    energyConsumerPhase: _EnergyConsumerPhase_pb2.EnergyConsumerPhase
    energySource: _EnergySource_pb2.EnergySource
    energySourcePhase: _EnergySourcePhase_pb2.EnergySourcePhase
    fuse: _Fuse_pb2.Fuse
    jumper: _Jumper_pb2.Jumper
    junction: _Junction_pb2.Junction
    linearShuntCompensator: _LinearShuntCompensator_pb2.LinearShuntCompensator
    perLengthSequenceImpedance: _PerLengthSequenceImpedance_pb2.PerLengthSequenceImpedance
    powerTransformer: _PowerTransformer_pb2.PowerTransformer
    powerTransformerEnd: _PowerTransformerEnd_pb2.PowerTransformerEnd
    ratioTapChanger: _RatioTapChanger_pb2.RatioTapChanger
    recloser: _Recloser_pb2.Recloser
    circuit: _Circuit_pb2.Circuit
    loop: _Loop_pb2.Loop
    pole: _Pole_pb2.Pole
    streetlight: _Streetlight_pb2.Streetlight
    accumulator: _Accumulator_pb2.Accumulator
    analog: _Analog_pb2.Analog
    discrete: _Discrete_pb2.Discrete
    control: _Control_pb2.Control
    remoteControl: _RemoteControl_pb2.RemoteControl
    remoteSource: _RemoteSource_pb2.RemoteSource
    powerTransformerInfo: _PowerTransformerInfo_pb2.PowerTransformerInfo
    powerElectronicsConnection: _PowerElectronicsConnection_pb2.PowerElectronicsConnection
    powerElectronicsConnectionPhase: _PowerElectronicsConnectionPhase_pb2.PowerElectronicsConnectionPhase
    batteryUnit: _BatteryUnit_pb2.BatteryUnit
    photoVoltaicUnit: _PhotoVoltaicUnit_pb2.PhotoVoltaicUnit
    powerElectronicsWindUnit: _PowerElectronicsWindUnit_pb2.PowerElectronicsWindUnit
    busbarSection: _BusbarSection_pb2.BusbarSection
    loadBreakSwitch: _LoadBreakSwitch_pb2.LoadBreakSwitch
    transformerStarImpedance: _TransformerStarImpedance_pb2.TransformerStarImpedance
    transformerEndInfo: _TransformerEndInfo_pb2.TransformerEndInfo
    transformerTankInfo: _TransformerTankInfo_pb2.TransformerTankInfo
    noLoadTest: _NoLoadTest_pb2.NoLoadTest
    openCircuitTest: _OpenCircuitTest_pb2.OpenCircuitTest
    shortCircuitTest: _ShortCircuitTest_pb2.ShortCircuitTest
    equivalentBranch: _EquivalentBranch_pb2.EquivalentBranch
    shuntCompensatorInfo: _ShuntCompensatorInfo_pb2.ShuntCompensatorInfo
    lvFeeder: _LvFeeder_pb2.LvFeeder
    currentTransformer: _CurrentTransformer_pb2.CurrentTransformer
    potentialTransformer: _PotentialTransformer_pb2.PotentialTransformer
    currentTransformerInfo: _CurrentTransformerInfo_pb2.CurrentTransformerInfo
    potentialTransformerInfo: _PotentialTransformerInfo_pb2.PotentialTransformerInfo
    switchInfo: _SwitchInfo_pb2.SwitchInfo
    relayInfo: _RelayInfo_pb2.RelayInfo
    currentRelay: _CurrentRelay_pb2.CurrentRelay
    tapChangerControl: _TapChangerControl_pb2.TapChangerControl
    evChargingUnit: _EvChargingUnit_pb2.EvChargingUnit
    seriesCompensator: _SeriesCompensator_pb2.SeriesCompensator
    ground: _Ground_pb2.Ground
    groundDisconnector: _GroundDisconnector_pb2.GroundDisconnector
    protectionRelayScheme: _ProtectionRelayScheme_pb2.ProtectionRelayScheme
    protectionRelaySystem: _ProtectionRelaySystem_pb2.ProtectionRelaySystem
    voltageRelay: _VoltageRelay_pb2.VoltageRelay
    distanceRelay: _DistanceRelay_pb2.DistanceRelay
    synchronousMachine: _SynchronousMachine_pb2.SynchronousMachine
    reactiveCapabilityCurve: _ReactiveCapabilityCurve_pb2.ReactiveCapabilityCurve
    groundingImpedance: _GroundingImpedance_pb2.GroundingImpedance
    petersenCoil: _PetersenCoil_pb2.PetersenCoil
    staticVarCompensator: _StaticVarCompensator_pb2.StaticVarCompensator
    panDemandResponseFunction: _PanDemandResponseFunction_pb2.PanDemandResponseFunction
    batteryControl: _BatteryControl_pb2.BatteryControl
    perLengthPhaseImpedance: _PerLengthPhaseImpedance_pb2.PerLengthPhaseImpedance
    cut: _Cut_pb2.Cut
    clamp: _Clamp_pb2.Clamp
    directionalCurrentRelay: _DirectionalCurrentRelay_pb2.DirectionalCurrentRelay
    other: _any_pb2.Any
    def __init__(self, cableInfo: _Optional[_Union[_CableInfo_pb2.CableInfo, _Mapping]] = ..., overheadWireInfo: _Optional[_Union[_OverheadWireInfo_pb2.OverheadWireInfo, _Mapping]] = ..., assetOwner: _Optional[_Union[_AssetOwner_pb2.AssetOwner, _Mapping]] = ..., organisation: _Optional[_Union[_Organisation_pb2.Organisation, _Mapping]] = ..., location: _Optional[_Union[_Location_pb2.Location, _Mapping]] = ..., meter: _Optional[_Union[_Meter_pb2.Meter, _Mapping]] = ..., usagePoint: _Optional[_Union[_UsagePoint_pb2.UsagePoint, _Mapping]] = ..., operationalRestriction: _Optional[_Union[_OperationalRestriction_pb2.OperationalRestriction, _Mapping]] = ..., faultIndicator: _Optional[_Union[_FaultIndicator_pb2.FaultIndicator, _Mapping]] = ..., baseVoltage: _Optional[_Union[_BaseVoltage_pb2.BaseVoltage, _Mapping]] = ..., connectivityNode: _Optional[_Union[_ConnectivityNode_pb2.ConnectivityNode, _Mapping]] = ..., feeder: _Optional[_Union[_Feeder_pb2.Feeder, _Mapping]] = ..., geographicalRegion: _Optional[_Union[_GeographicalRegion_pb2.GeographicalRegion, _Mapping]] = ..., site: _Optional[_Union[_Site_pb2.Site, _Mapping]] = ..., subGeographicalRegion: _Optional[_Union[_SubGeographicalRegion_pb2.SubGeographicalRegion, _Mapping]] = ..., substation: _Optional[_Union[_Substation_pb2.Substation, _Mapping]] = ..., terminal: _Optional[_Union[_Terminal_pb2.Terminal, _Mapping]] = ..., acLineSegment: _Optional[_Union[_AcLineSegment_pb2.AcLineSegment, _Mapping]] = ..., breaker: _Optional[_Union[_Breaker_pb2.Breaker, _Mapping]] = ..., disconnector: _Optional[_Union[_Disconnector_pb2.Disconnector, _Mapping]] = ..., energyConsumer: _Optional[_Union[_EnergyConsumer_pb2.EnergyConsumer, _Mapping]] = ..., energyConsumerPhase: _Optional[_Union[_EnergyConsumerPhase_pb2.EnergyConsumerPhase, _Mapping]] = ..., energySource: _Optional[_Union[_EnergySource_pb2.EnergySource, _Mapping]] = ..., energySourcePhase: _Optional[_Union[_EnergySourcePhase_pb2.EnergySourcePhase, _Mapping]] = ..., fuse: _Optional[_Union[_Fuse_pb2.Fuse, _Mapping]] = ..., jumper: _Optional[_Union[_Jumper_pb2.Jumper, _Mapping]] = ..., junction: _Optional[_Union[_Junction_pb2.Junction, _Mapping]] = ..., linearShuntCompensator: _Optional[_Union[_LinearShuntCompensator_pb2.LinearShuntCompensator, _Mapping]] = ..., perLengthSequenceImpedance: _Optional[_Union[_PerLengthSequenceImpedance_pb2.PerLengthSequenceImpedance, _Mapping]] = ..., powerTransformer: _Optional[_Union[_PowerTransformer_pb2.PowerTransformer, _Mapping]] = ..., powerTransformerEnd: _Optional[_Union[_PowerTransformerEnd_pb2.PowerTransformerEnd, _Mapping]] = ..., ratioTapChanger: _Optional[_Union[_RatioTapChanger_pb2.RatioTapChanger, _Mapping]] = ..., recloser: _Optional[_Union[_Recloser_pb2.Recloser, _Mapping]] = ..., circuit: _Optional[_Union[_Circuit_pb2.Circuit, _Mapping]] = ..., loop: _Optional[_Union[_Loop_pb2.Loop, _Mapping]] = ..., pole: _Optional[_Union[_Pole_pb2.Pole, _Mapping]] = ..., streetlight: _Optional[_Union[_Streetlight_pb2.Streetlight, _Mapping]] = ..., accumulator: _Optional[_Union[_Accumulator_pb2.Accumulator, _Mapping]] = ..., analog: _Optional[_Union[_Analog_pb2.Analog, _Mapping]] = ..., discrete: _Optional[_Union[_Discrete_pb2.Discrete, _Mapping]] = ..., control: _Optional[_Union[_Control_pb2.Control, _Mapping]] = ..., remoteControl: _Optional[_Union[_RemoteControl_pb2.RemoteControl, _Mapping]] = ..., remoteSource: _Optional[_Union[_RemoteSource_pb2.RemoteSource, _Mapping]] = ..., powerTransformerInfo: _Optional[_Union[_PowerTransformerInfo_pb2.PowerTransformerInfo, _Mapping]] = ..., powerElectronicsConnection: _Optional[_Union[_PowerElectronicsConnection_pb2.PowerElectronicsConnection, _Mapping]] = ..., powerElectronicsConnectionPhase: _Optional[_Union[_PowerElectronicsConnectionPhase_pb2.PowerElectronicsConnectionPhase, _Mapping]] = ..., batteryUnit: _Optional[_Union[_BatteryUnit_pb2.BatteryUnit, _Mapping]] = ..., photoVoltaicUnit: _Optional[_Union[_PhotoVoltaicUnit_pb2.PhotoVoltaicUnit, _Mapping]] = ..., powerElectronicsWindUnit: _Optional[_Union[_PowerElectronicsWindUnit_pb2.PowerElectronicsWindUnit, _Mapping]] = ..., busbarSection: _Optional[_Union[_BusbarSection_pb2.BusbarSection, _Mapping]] = ..., loadBreakSwitch: _Optional[_Union[_LoadBreakSwitch_pb2.LoadBreakSwitch, _Mapping]] = ..., transformerStarImpedance: _Optional[_Union[_TransformerStarImpedance_pb2.TransformerStarImpedance, _Mapping]] = ..., transformerEndInfo: _Optional[_Union[_TransformerEndInfo_pb2.TransformerEndInfo, _Mapping]] = ..., transformerTankInfo: _Optional[_Union[_TransformerTankInfo_pb2.TransformerTankInfo, _Mapping]] = ..., noLoadTest: _Optional[_Union[_NoLoadTest_pb2.NoLoadTest, _Mapping]] = ..., openCircuitTest: _Optional[_Union[_OpenCircuitTest_pb2.OpenCircuitTest, _Mapping]] = ..., shortCircuitTest: _Optional[_Union[_ShortCircuitTest_pb2.ShortCircuitTest, _Mapping]] = ..., equivalentBranch: _Optional[_Union[_EquivalentBranch_pb2.EquivalentBranch, _Mapping]] = ..., shuntCompensatorInfo: _Optional[_Union[_ShuntCompensatorInfo_pb2.ShuntCompensatorInfo, _Mapping]] = ..., lvFeeder: _Optional[_Union[_LvFeeder_pb2.LvFeeder, _Mapping]] = ..., currentTransformer: _Optional[_Union[_CurrentTransformer_pb2.CurrentTransformer, _Mapping]] = ..., potentialTransformer: _Optional[_Union[_PotentialTransformer_pb2.PotentialTransformer, _Mapping]] = ..., currentTransformerInfo: _Optional[_Union[_CurrentTransformerInfo_pb2.CurrentTransformerInfo, _Mapping]] = ..., potentialTransformerInfo: _Optional[_Union[_PotentialTransformerInfo_pb2.PotentialTransformerInfo, _Mapping]] = ..., switchInfo: _Optional[_Union[_SwitchInfo_pb2.SwitchInfo, _Mapping]] = ..., relayInfo: _Optional[_Union[_RelayInfo_pb2.RelayInfo, _Mapping]] = ..., currentRelay: _Optional[_Union[_CurrentRelay_pb2.CurrentRelay, _Mapping]] = ..., tapChangerControl: _Optional[_Union[_TapChangerControl_pb2.TapChangerControl, _Mapping]] = ..., evChargingUnit: _Optional[_Union[_EvChargingUnit_pb2.EvChargingUnit, _Mapping]] = ..., seriesCompensator: _Optional[_Union[_SeriesCompensator_pb2.SeriesCompensator, _Mapping]] = ..., ground: _Optional[_Union[_Ground_pb2.Ground, _Mapping]] = ..., groundDisconnector: _Optional[_Union[_GroundDisconnector_pb2.GroundDisconnector, _Mapping]] = ..., protectionRelayScheme: _Optional[_Union[_ProtectionRelayScheme_pb2.ProtectionRelayScheme, _Mapping]] = ..., protectionRelaySystem: _Optional[_Union[_ProtectionRelaySystem_pb2.ProtectionRelaySystem, _Mapping]] = ..., voltageRelay: _Optional[_Union[_VoltageRelay_pb2.VoltageRelay, _Mapping]] = ..., distanceRelay: _Optional[_Union[_DistanceRelay_pb2.DistanceRelay, _Mapping]] = ..., synchronousMachine: _Optional[_Union[_SynchronousMachine_pb2.SynchronousMachine, _Mapping]] = ..., reactiveCapabilityCurve: _Optional[_Union[_ReactiveCapabilityCurve_pb2.ReactiveCapabilityCurve, _Mapping]] = ..., groundingImpedance: _Optional[_Union[_GroundingImpedance_pb2.GroundingImpedance, _Mapping]] = ..., petersenCoil: _Optional[_Union[_PetersenCoil_pb2.PetersenCoil, _Mapping]] = ..., staticVarCompensator: _Optional[_Union[_StaticVarCompensator_pb2.StaticVarCompensator, _Mapping]] = ..., panDemandResponseFunction: _Optional[_Union[_PanDemandResponseFunction_pb2.PanDemandResponseFunction, _Mapping]] = ..., batteryControl: _Optional[_Union[_BatteryControl_pb2.BatteryControl, _Mapping]] = ..., perLengthPhaseImpedance: _Optional[_Union[_PerLengthPhaseImpedance_pb2.PerLengthPhaseImpedance, _Mapping]] = ..., cut: _Optional[_Union[_Cut_pb2.Cut, _Mapping]] = ..., clamp: _Optional[_Union[_Clamp_pb2.Clamp, _Mapping]] = ..., directionalCurrentRelay: _Optional[_Union[_DirectionalCurrentRelay_pb2.DirectionalCurrentRelay, _Mapping]] = ..., other: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
