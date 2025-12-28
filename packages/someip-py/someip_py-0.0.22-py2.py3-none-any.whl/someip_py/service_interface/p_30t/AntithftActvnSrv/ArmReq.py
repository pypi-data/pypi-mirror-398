from someip_py.codec import *


class IdtArmReq(SomeIpPayload):

    IdtArmReq: Uint8

    def __init__(self):

        self.IdtArmReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
