from someip_py.codec import *


class IdtSettingAPAInfoKls(SomeIpPayload):

    SettingAPAInfoSeN: Uint8

    ApaEnableParkOutButtonStateSeN: Uint8

    ApaParkSpdButtonStateSeN: Uint8

    APAGearActParkInSwitchSeN: Uint8

    APAGearActParkOutSwitchSeN: Uint8

    def __init__(self):

        self.SettingAPAInfoSeN = Uint8()

        self.ApaEnableParkOutButtonStateSeN = Uint8()

        self.ApaParkSpdButtonStateSeN = Uint8()

        self.APAGearActParkInSwitchSeN = Uint8()

        self.APAGearActParkOutSwitchSeN = Uint8()


class IdtSettingAPAInfo(SomeIpPayload):

    IdtSettingAPAInfo: IdtSettingAPAInfoKls

    def __init__(self):

        self.IdtSettingAPAInfo = IdtSettingAPAInfoKls()
