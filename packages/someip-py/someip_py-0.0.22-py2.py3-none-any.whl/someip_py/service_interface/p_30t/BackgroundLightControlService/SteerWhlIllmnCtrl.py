from someip_py.codec import *


class IdtOnOffSwtLi(SomeIpPayload):

    IdtOnOffSwtLi: Bool

    def __init__(self):

        self.IdtOnOffSwtLi = Bool()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
