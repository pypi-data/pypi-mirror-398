from someip_py.codec import *


class IdtSettingCheckKls(SomeIpPayload):

    SettingDataErrorSeN: Uint8

    SettingSyncReqSeN: Uint8

    def __init__(self):

        self.SettingDataErrorSeN = Uint8()

        self.SettingSyncReqSeN = Uint8()


class IdtSettingCheck(SomeIpPayload):

    IdtSettingCheck: IdtSettingCheckKls

    def __init__(self):

        self.IdtSettingCheck = IdtSettingCheckKls()
