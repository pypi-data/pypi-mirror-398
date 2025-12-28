from someip_py.codec import *


class IdtADUSItem(SomeIpPayload):

    Key: Uint16

    Value: Int16

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int16()


class IdtSettingInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    CRCValueSeN: Uint8

    NzpSwitchSeN: Uint8

    ChangeLaneConfirmSwtichSeN: Uint8

    NZPLaneChangeWarning: Uint8

    LaneChangeStyle: Uint8

    SpeedLimitOffsetOptionSeN: Uint8

    SpeedLimitOffsetSeN: Int8

    LCCSwitchSeN: Uint8

    ALCSwitch: Uint8

    AutoAlignSpeedLimit: Uint8

    AlignedSpeedSetting: Uint8

    FCWSettingSeN: Uint8

    AEBSwitchSeN: Uint8

    LDWSettingSeN: Uint8

    LDPSwitchSeN: Uint8

    ELKASwitch: Uint8

    FCTASwitchSeN: Uint8

    FCTASettingSeN: Uint8

    RCTASwitchSeN: Uint8

    DOWSwitchSeN: Uint8

    BSDSwitchSeN: Uint8

    BsdWarningSetting: Uint8

    CVWSwitch: Uint8

    TSISwitchSeN: Uint8

    TSISettingSeN: Uint8

    TSISettingOffsetOptionSeN: Uint8

    TSILimitOffsetValueSeN: Int8

    TSRSwitchSeN: Uint8

    SRVSwitchSeN: Uint8

    EMASwitchSeN: Uint8

    TLASwitchSeN: Uint8

    TLAWarningSwitch: Uint8

    CMSRSwitchSeN: Uint8

    VoiceWarningOptionSeN: Uint8

    APASwitchSeN: Uint8

    RSPASwitchSeN: Uint8

    RPASwitchSeN: Uint8

    LPSwitchSeN: Uint8

    PebSwitchSetting: Uint8

    FrontVehGoSeN: Uint8

    TSILimitOffsetAbsoluteValueSeN: Int8

    SpeedLimitOffsetAbsoluteSeN: Int8

    LDWSwitch: Uint8

    ACPESwitchSeN: Uint8

    FCWSwitch: Uint8

    FCWPlusSwitch: Uint8

    AEBPlusSwitch: Uint8

    NzpUbSwitchSeN: Uint8

    AWWSwitchSeN: Uint8

    IAccRoadFeaSwitchSeN: Uint8

    IAccUndPreSwitchSeN: Uint8

    QuickActiveSwitchSeN: Uint8

    RMFSwitchSeN: Uint8

    LSSSettingSeN: Uint8

    LDPTypeSeN: Uint8

    APAGearActParkInSwitchSeN: Uint8

    APAGearActParkOutSwitchSeN: Uint8

    AESSwitchSeN: Uint8

    ADModeOptionSeN: Uint8

    SteeringWheelSettingTypeSeN: Uint8

    FVSWSwitchSeN: Uint8

    ADUSItemsSeN: SomeIpDynamicSizeArray[IdtADUSItem]

    def __init__(self):

        self.CRCValueSeN = Uint8()

        self.NzpSwitchSeN = Uint8()

        self.ChangeLaneConfirmSwtichSeN = Uint8()

        self.NZPLaneChangeWarning = Uint8()

        self.LaneChangeStyle = Uint8()

        self.SpeedLimitOffsetOptionSeN = Uint8()

        self.SpeedLimitOffsetSeN = Int8()

        self.LCCSwitchSeN = Uint8()

        self.ALCSwitch = Uint8()

        self.AutoAlignSpeedLimit = Uint8()

        self.AlignedSpeedSetting = Uint8()

        self.FCWSettingSeN = Uint8()

        self.AEBSwitchSeN = Uint8()

        self.LDWSettingSeN = Uint8()

        self.LDPSwitchSeN = Uint8()

        self.ELKASwitch = Uint8()

        self.FCTASwitchSeN = Uint8()

        self.FCTASettingSeN = Uint8()

        self.RCTASwitchSeN = Uint8()

        self.DOWSwitchSeN = Uint8()

        self.BSDSwitchSeN = Uint8()

        self.BsdWarningSetting = Uint8()

        self.CVWSwitch = Uint8()

        self.TSISwitchSeN = Uint8()

        self.TSISettingSeN = Uint8()

        self.TSISettingOffsetOptionSeN = Uint8()

        self.TSILimitOffsetValueSeN = Int8()

        self.TSRSwitchSeN = Uint8()

        self.SRVSwitchSeN = Uint8()

        self.EMASwitchSeN = Uint8()

        self.TLASwitchSeN = Uint8()

        self.TLAWarningSwitch = Uint8()

        self.CMSRSwitchSeN = Uint8()

        self.VoiceWarningOptionSeN = Uint8()

        self.APASwitchSeN = Uint8()

        self.RSPASwitchSeN = Uint8()

        self.RPASwitchSeN = Uint8()

        self.LPSwitchSeN = Uint8()

        self.PebSwitchSetting = Uint8()

        self.FrontVehGoSeN = Uint8()

        self.TSILimitOffsetAbsoluteValueSeN = Int8()

        self.SpeedLimitOffsetAbsoluteSeN = Int8()

        self.LDWSwitch = Uint8()

        self.ACPESwitchSeN = Uint8()

        self.FCWSwitch = Uint8()

        self.FCWPlusSwitch = Uint8()

        self.AEBPlusSwitch = Uint8()

        self.NzpUbSwitchSeN = Uint8()

        self.AWWSwitchSeN = Uint8()

        self.IAccRoadFeaSwitchSeN = Uint8()

        self.IAccUndPreSwitchSeN = Uint8()

        self.QuickActiveSwitchSeN = Uint8()

        self.RMFSwitchSeN = Uint8()

        self.LSSSettingSeN = Uint8()

        self.LDPTypeSeN = Uint8()

        self.APAGearActParkInSwitchSeN = Uint8()

        self.APAGearActParkOutSwitchSeN = Uint8()

        self.AESSwitchSeN = Uint8()

        self.ADModeOptionSeN = Uint8()

        self.SteeringWheelSettingTypeSeN = Uint8()

        self.FVSWSwitchSeN = Uint8()

        self.ADUSItemsSeN = SomeIpDynamicSizeArray(IdtADUSItem)


class IdtSettingInfo(SomeIpPayload):

    IdtSettingInfo: IdtSettingInfoKls

    def __init__(self):

        self.IdtSettingInfo = IdtSettingInfoKls()
