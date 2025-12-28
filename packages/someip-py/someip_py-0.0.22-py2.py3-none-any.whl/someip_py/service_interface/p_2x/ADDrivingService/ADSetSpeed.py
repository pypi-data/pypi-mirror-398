from someip_py.codec import *


class IdtADSetSpeedKls(SomeIpPayload):

    SetSpeedOpTypeSeN: Uint8

    SetSpeedStepSeN: Int8

    SetSpeedValueSeN: Uint8

    def __init__(self):

        self.SetSpeedOpTypeSeN = Uint8()

        self.SetSpeedStepSeN = Int8()

        self.SetSpeedValueSeN = Uint8()


class IdtADSetSpeed(SomeIpPayload):

    IdtADSetSpeed: IdtADSetSpeedKls

    def __init__(self):

        self.IdtADSetSpeed = IdtADSetSpeedKls()


class IdtADSetSpeedRet(SomeIpPayload):

    IdtADSetSpeedRet: Uint8

    def __init__(self):

        self.IdtADSetSpeedRet = Uint8()
