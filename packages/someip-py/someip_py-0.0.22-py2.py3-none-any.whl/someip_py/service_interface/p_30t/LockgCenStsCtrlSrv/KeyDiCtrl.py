from someip_py.codec import *


class IdtKeyDiReq(SomeIpPayload):

    IdtKeyDiReq: Uint8

    def __init__(self):

        self.IdtKeyDiReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
