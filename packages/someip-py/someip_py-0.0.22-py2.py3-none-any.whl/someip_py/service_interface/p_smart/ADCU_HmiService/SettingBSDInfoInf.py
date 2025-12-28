from someip_py.codec import *


class SettingBSDInfoKls(SomeIpPayload):

    BSDSwitchSeN: Uint8

    BsdWarningSetting: Uint8

    CVWSwitch: Uint8

    def __init__(self):

        self.BSDSwitchSeN = Uint8()

        self.BsdWarningSetting = Uint8()

        self.CVWSwitch = Uint8()


class SettingBSDInfo(SomeIpPayload):

    SettingBSDInfo: SettingBSDInfoKls

    def __init__(self):

        self.SettingBSDInfo = SettingBSDInfoKls()
