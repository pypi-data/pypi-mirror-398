from someip_py.codec import *


class IdtADSetSpeedKls(SomeIpPayload):

    _include_struct_len = True

    OpType: Uint8

    Step: Int8

    Value: Uint8

    def __init__(self):

        self.OpType = Uint8()

        self.Step = Int8()

        self.Value = Uint8()


class IdtADSetSpeed(SomeIpPayload):

    IdtADSetSpeed: IdtADSetSpeedKls

    def __init__(self):

        self.IdtADSetSpeed = IdtADSetSpeedKls()


class IdtADSetSpeedRet(SomeIpPayload):

    IdtADSetSpeedRet: Uint8

    def __init__(self):

        self.IdtADSetSpeedRet = Uint8()
