from someip_py.codec import *


class SettingRCTABInfo(SomeIpPayload):

    SettingRCTABInfo: Uint8

    def __init__(self):

        self.SettingRCTABInfo = Uint8()
