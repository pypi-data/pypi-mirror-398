from someip_py.codec import *


class IdtAmbienceTORCtrl(SomeIpPayload):

    IdtAmbienceTORCtrl: Uint8

    def __init__(self):

        self.IdtAmbienceTORCtrl = Uint8()


class IdtOnOffSwtLi(SomeIpPayload):

    IdtOnOffSwtLi: Bool

    def __init__(self):

        self.IdtOnOffSwtLi = Bool()


class IdtAmbienceAppReturnCode(SomeIpPayload):

    IdtAmbienceAppReturnCode: Uint8

    def __init__(self):

        self.IdtAmbienceAppReturnCode = Uint8()
