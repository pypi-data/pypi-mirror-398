from someip_py.codec import *


class SettingTSIInfoKls(SomeIpPayload):

    TSISwitchSeN: Uint8

    TSISettingSeN: Uint8

    TSISettingOffsetOptionSeN: Uint8

    TSILimitOffsetValueSeN: Int8

    TSRSwitchSeN: Uint8

    TSIUpdateSwitchSeN: Uint8

    def __init__(self):

        self.TSISwitchSeN = Uint8()

        self.TSISettingSeN = Uint8()

        self.TSISettingOffsetOptionSeN = Uint8()

        self.TSILimitOffsetValueSeN = Int8()

        self.TSRSwitchSeN = Uint8()

        self.TSIUpdateSwitchSeN = Uint8()


class SettingTSIInfo(SomeIpPayload):

    SettingTSIInfo: SettingTSIInfoKls

    def __init__(self):

        self.SettingTSIInfo = SettingTSIInfoKls()
