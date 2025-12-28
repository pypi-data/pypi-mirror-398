from someip_py.codec import *


class SettingAEBInfoKls(SomeIpPayload):

    FCWSettingSeN: Uint8

    AEBSwitchSeN: Uint8

    def __init__(self):

        self.FCWSettingSeN = Uint8()

        self.AEBSwitchSeN = Uint8()


class SettingAEBInfo(SomeIpPayload):

    SettingAEBInfo: SettingAEBInfoKls

    def __init__(self):

        self.SettingAEBInfo = SettingAEBInfoKls()
