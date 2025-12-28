from someip_py.codec import *


class SettingDrivingInfoKls(SomeIpPayload):

    NzpSwitchSeN: Uint8

    ChangeLaneConfirmSwtichSeN: Uint8

    NZPLaneChangeWarning: Uint8

    LaneChangeStyle: Uint8

    SpeedLimitOffsetOptionSeN: Uint8

    SpeedLimitOffsetSeN: Int8

    LCCSwitchSeN: Uint8

    ALCSwitch: Uint8

    AutoAlignSpeedLimit: Uint8

    SpeedLimitOffsetAbsoluteSeN: Int8

    NzpUbSwitchSeN: Uint8

    IAccRoadFeaSwitchSeN: Uint8

    IAccUndPreSwitchSeN: Uint8

    QuickActiveSwitchSeN: Uint8

    ADModeOptionSeN: Uint8

    SteeringWheelSettingTypeSeN: Uint8

    def __init__(self):

        self.NzpSwitchSeN = Uint8()

        self.ChangeLaneConfirmSwtichSeN = Uint8()

        self.NZPLaneChangeWarning = Uint8()

        self.LaneChangeStyle = Uint8()

        self.SpeedLimitOffsetOptionSeN = Uint8()

        self.SpeedLimitOffsetSeN = Int8()

        self.LCCSwitchSeN = Uint8()

        self.ALCSwitch = Uint8()

        self.AutoAlignSpeedLimit = Uint8()

        self.SpeedLimitOffsetAbsoluteSeN = Int8()

        self.NzpUbSwitchSeN = Uint8()

        self.IAccRoadFeaSwitchSeN = Uint8()

        self.IAccUndPreSwitchSeN = Uint8()

        self.QuickActiveSwitchSeN = Uint8()

        self.ADModeOptionSeN = Uint8()

        self.SteeringWheelSettingTypeSeN = Uint8()


class SettingDrivingInfo(SomeIpPayload):

    SettingDrivingInfo: SettingDrivingInfoKls

    def __init__(self):

        self.SettingDrivingInfo = SettingDrivingInfoKls()
