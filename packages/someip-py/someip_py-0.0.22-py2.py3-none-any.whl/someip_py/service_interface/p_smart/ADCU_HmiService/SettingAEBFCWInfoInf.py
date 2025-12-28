from someip_py.codec import *


class SettingAEBFCWInfoKls(SomeIpPayload):

    AEBFCWGrey: Uint8

    AEBFCWswitch: Uint8

    def __init__(self):

        self.AEBFCWGrey = Uint8()

        self.AEBFCWswitch = Uint8()


class SettingAEBFCWInfo(SomeIpPayload):

    SettingAEBFCWInfo: SettingAEBFCWInfoKls

    def __init__(self):

        self.SettingAEBFCWInfo = SettingAEBFCWInfoKls()
