from someip_py.codec import *


class SettingTLAInfoKls(SomeIpPayload):

    TLASwitchSeN: Uint8

    TLAWarningSwitch: Uint8

    def __init__(self):

        self.TLASwitchSeN = Uint8()

        self.TLAWarningSwitch = Uint8()


class SettingTLAInfo(SomeIpPayload):

    SettingTLAInfo: SettingTLAInfoKls

    def __init__(self):

        self.SettingTLAInfo = SettingTLAInfoKls()
