from someip_py.codec import *


class IdtTrOpenPosnReq(SomeIpPayload):

    IdtTrOpenPosnReq: Uint8

    def __init__(self):

        self.IdtTrOpenPosnReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
