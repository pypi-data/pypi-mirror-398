from someip_py.codec import *


class SettingFCTAInfoKls(SomeIpPayload):

    FCTASwitchSeN: Uint8

    FCTASettingSeN: Uint8

    def __init__(self):

        self.FCTASwitchSeN = Uint8()

        self.FCTASettingSeN = Uint8()


class SettingFCTAInfo(SomeIpPayload):

    SettingFCTAInfo: SettingFCTAInfoKls

    def __init__(self):

        self.SettingFCTAInfo = SettingFCTAInfoKls()
