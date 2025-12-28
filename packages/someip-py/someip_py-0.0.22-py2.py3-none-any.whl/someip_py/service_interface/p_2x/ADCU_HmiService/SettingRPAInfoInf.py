from someip_py.codec import *


class SettingRPAInfoKls(SomeIpPayload):

    RSPASwitchSeN: Uint8

    RPASwitchSeN: Uint8

    def __init__(self):

        self.RSPASwitchSeN = Uint8()

        self.RPASwitchSeN = Uint8()


class SettingRPAInfo(SomeIpPayload):

    SettingRPAInfo: SettingRPAInfoKls

    def __init__(self):

        self.SettingRPAInfo = SettingRPAInfoKls()
