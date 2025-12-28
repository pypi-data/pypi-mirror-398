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


class SettingDrivingInfo(SomeIpPayload):

    SettingDrivingInfo: SettingDrivingInfoKls

    def __init__(self):

        self.SettingDrivingInfo = SettingDrivingInfoKls()
