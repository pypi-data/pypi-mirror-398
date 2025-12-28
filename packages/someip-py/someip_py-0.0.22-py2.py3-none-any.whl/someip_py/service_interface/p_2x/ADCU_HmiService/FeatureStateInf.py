from someip_py.codec import *


class FctaRisk(SomeIpPayload):

    FctaRiskSectorColor: Uint8

    FctaRiskSectorOrientation: Uint8

    def __init__(self):

        self.FctaRiskSectorColor = Uint8()

        self.FctaRiskSectorOrientation = Uint8()


class BsdRisk(SomeIpPayload):

    BsdRiskSectorColor: Uint8

    BsdRiskSectorOrientation: Uint8

    def __init__(self):

        self.BsdRiskSectorColor = Uint8()

        self.BsdRiskSectorOrientation = Uint8()


class RCATRisk(SomeIpPayload):

    RCATArrowLevelSeN: Uint8

    RctaArrowOrientationSeN: Uint8

    def __init__(self):

        self.RCATArrowLevelSeN = Uint8()

        self.RctaArrowOrientationSeN = Uint8()


class DowRisk(SomeIpPayload):

    DowDangerSourceSeN: Uint8

    DOWDangerLevel: Uint8

    def __init__(self):

        self.DowDangerSourceSeN = Uint8()

        self.DOWDangerLevel = Uint8()


class SensorStatus(SomeIpPayload):

    SensorIDSeN: Uint32

    PerSensorStateSeN: Uint8

    SensorReasonSeN: Uint32

    def __init__(self):

        self.SensorIDSeN = Uint32()

        self.PerSensorStateSeN = Uint8()

        self.SensorReasonSeN = Uint32()


class AVPStatus(SomeIpPayload):

    AVPStageSeN: Uint8

    AVPFirstTurnSeN: Uint8

    AVPFirstTurnDistanceSeN: Int16

    AVPCrusingProgressSeN: Int8

    AVPCrusingReDistanceSeN: Uint16

    FinishLearningButtonSeN: Uint8

    AVPIconSeN: Uint8

    AVPButtonSeN: Uint8

    def __init__(self):

        self.AVPStageSeN = Uint8()

        self.AVPFirstTurnSeN = Uint8()

        self.AVPFirstTurnDistanceSeN = Int16()

        self.AVPCrusingProgressSeN = Int8()

        self.AVPCrusingReDistanceSeN = Uint16()

        self.FinishLearningButtonSeN = Uint8()

        self.AVPIconSeN = Uint8()

        self.AVPButtonSeN = Uint8()


class AWWRiskType(SomeIpPayload):

    AWWStatusFLSeN: Uint8

    AWWStatusFRSeN: Uint8

    AWWStatusRLSeN: Uint8

    AWWStatusRRSeN: Uint8

    def __init__(self):

        self.AWWStatusFLSeN = Uint8()

        self.AWWStatusFRSeN = Uint8()

        self.AWWStatusRLSeN = Uint8()

        self.AWWStatusRRSeN = Uint8()


class FeatureStateKls(SomeIpPayload):
    _has_dynamic_size = True

    NzpStateSeN: Uint8

    ApaStateSeN: Uint8

    MaxCruiseSpeedSeN: Uint16

    AvailableSlotIDSeN: SomeIpDynamicSizeArray[Uint32]

    LaneSpeedLimitSeN: Uint16

    TimeGapApplyEnableSeN: Uint8

    SuspendTimeSeN: Uint16

    ParkContinueButtonSeN: Uint8

    StartParkButtonStateSeN: Uint8

    LCCStateSeN: Uint8

    ACCStateSeN: Uint8

    RapaState: Uint8

    LaneChangeStatusSeN: Uint8

    ParkingWaitFlagSeN: Uint8

    SearchingGearStatusSeN: Uint8

    SelectSlotBttonStateSeN: Uint8

    FctaRiskSectorSeN: SomeIpDynamicSizeArray[FctaRisk]

    BsdRiskSectorSeN: SomeIpDynamicSizeArray[BsdRisk]

    RCATArrowSeN: SomeIpDynamicSizeArray[RCATRisk]

    DowDangerSeN: SomeIpDynamicSizeArray[DowRisk]

    RcwAlarmLevelSeN: Uint8

    TSISpeedLimitIconSeN: Uint8

    TSIIconFlickerSeN: Uint8

    TSIElectronicEyeIconSeN: Uint8

    TSINoOvertatingSeN: Uint8

    TLAFirstVehGNLightSeN: Uint8

    TLATrafficLightCountdownSeN: Int16

    TLATrafficLightLevelSeN: Uint8

    TLALeftSignalLampSeN: Uint8

    TLAStrightSignalLampSeN: Uint8

    TLARightSignalLampSeN: Uint8

    TLATurnSignalLamp: Uint8

    TLATurnLeftSignalLamp: Uint8

    TLAStarttogoSeN: Uint8

    TSRWarningTypeSeN: Uint8

    PEBFaultAlarm: Uint8

    PEBRain: Uint8

    PEBActive: Uint8

    LkaHandsOffWarning: Uint8

    FunctionPending: Uint8

    AxialAcceleration: Float32

    OnlineCalibState: Uint8

    OnlineCalibProgress: Uint8

    ADSensorStatusSeN: SomeIpDynamicSizeArray[SensorStatus]

    TSIElectronicEyeLenth: Int32

    ApaAvailableSlotParkingModeSeN: Uint8

    RecommendSlotlD: Uint8

    NextMaxCruiseSpeedSeN: Uint16

    StartReParkButtonStateSeN: Uint8

    ReturnReParkButtonStateSeN: Uint8

    AVPStatusSeN: AVPStatus

    ApaParkingStatusSeN: Uint8

    ApaAvailableDirectionSeN: SomeIpDynamicSizeArray[Uint8]

    ApaRecommendDirectionSeN: Uint8

    StartParkoutButtonStateSeN: Uint8

    ApaArticleDisplaySeN: SomeIpDynamicSizeArray[Uint8]

    AWWRiskSeN: AWWRiskType

    ALCAStateSeN: Uint8

    IAccSpeedAdaptSeN: Uint8

    LaneSpeedLimitSecSeN: Uint32

    def __init__(self):

        self.NzpStateSeN = Uint8()

        self.ApaStateSeN = Uint8()

        self.MaxCruiseSpeedSeN = Uint16()

        self.AvailableSlotIDSeN = SomeIpDynamicSizeArray(Uint32)

        self.LaneSpeedLimitSeN = Uint16()

        self.TimeGapApplyEnableSeN = Uint8()

        self.SuspendTimeSeN = Uint16()

        self.ParkContinueButtonSeN = Uint8()

        self.StartParkButtonStateSeN = Uint8()

        self.LCCStateSeN = Uint8()

        self.ACCStateSeN = Uint8()

        self.RapaState = Uint8()

        self.LaneChangeStatusSeN = Uint8()

        self.ParkingWaitFlagSeN = Uint8()

        self.SearchingGearStatusSeN = Uint8()

        self.SelectSlotBttonStateSeN = Uint8()

        self.FctaRiskSectorSeN = SomeIpDynamicSizeArray(FctaRisk)

        self.BsdRiskSectorSeN = SomeIpDynamicSizeArray(BsdRisk)

        self.RCATArrowSeN = SomeIpDynamicSizeArray(RCATRisk)

        self.DowDangerSeN = SomeIpDynamicSizeArray(DowRisk)

        self.RcwAlarmLevelSeN = Uint8()

        self.TSISpeedLimitIconSeN = Uint8()

        self.TSIIconFlickerSeN = Uint8()

        self.TSIElectronicEyeIconSeN = Uint8()

        self.TSINoOvertatingSeN = Uint8()

        self.TLAFirstVehGNLightSeN = Uint8()

        self.TLATrafficLightCountdownSeN = Int16()

        self.TLATrafficLightLevelSeN = Uint8()

        self.TLALeftSignalLampSeN = Uint8()

        self.TLAStrightSignalLampSeN = Uint8()

        self.TLARightSignalLampSeN = Uint8()

        self.TLATurnSignalLamp = Uint8()

        self.TLATurnLeftSignalLamp = Uint8()

        self.TLAStarttogoSeN = Uint8()

        self.TSRWarningTypeSeN = Uint8()

        self.PEBFaultAlarm = Uint8()

        self.PEBRain = Uint8()

        self.PEBActive = Uint8()

        self.LkaHandsOffWarning = Uint8()

        self.FunctionPending = Uint8()

        self.AxialAcceleration = Float32()

        self.OnlineCalibState = Uint8()

        self.OnlineCalibProgress = Uint8()

        self.ADSensorStatusSeN = SomeIpDynamicSizeArray(SensorStatus)

        self.TSIElectronicEyeLenth = Int32()

        self.ApaAvailableSlotParkingModeSeN = Uint8()

        self.RecommendSlotlD = Uint8()

        self.NextMaxCruiseSpeedSeN = Uint16()

        self.StartReParkButtonStateSeN = Uint8()

        self.ReturnReParkButtonStateSeN = Uint8()

        self.AVPStatusSeN = AVPStatus()

        self.ApaParkingStatusSeN = Uint8()

        self.ApaAvailableDirectionSeN = SomeIpDynamicSizeArray(Uint8)

        self.ApaRecommendDirectionSeN = Uint8()

        self.StartParkoutButtonStateSeN = Uint8()

        self.ApaArticleDisplaySeN = SomeIpDynamicSizeArray(Uint8)

        self.AWWRiskSeN = AWWRiskType()

        self.ALCAStateSeN = Uint8()

        self.IAccSpeedAdaptSeN = Uint8()

        self.LaneSpeedLimitSecSeN = Uint32()


class FeatureState(SomeIpPayload):

    FeatureState: FeatureStateKls

    def __init__(self):

        self.FeatureState = FeatureStateKls()
