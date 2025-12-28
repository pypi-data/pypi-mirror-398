from someip_py.codec import *


class SettingAEBInfoKls(SomeIpPayload):

    FCWSettingSeN: Uint8

    AEBSwitchSeN: Uint8

    FCWSwitch: Uint8

    FCWPlusSwitch: Uint8

    AEBPlusSwitch: Uint8

    def __init__(self):

        self.FCWSettingSeN = Uint8()

        self.AEBSwitchSeN = Uint8()

        self.FCWSwitch = Uint8()

        self.FCWPlusSwitch = Uint8()

        self.AEBPlusSwitch = Uint8()


class SettingAEBInfo(SomeIpPayload):

    SettingAEBInfo: SettingAEBInfoKls

    def __init__(self):

        self.SettingAEBInfo = SettingAEBInfoKls()
