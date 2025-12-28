from someip_py.codec import *


class IdtTrLockReq(SomeIpPayload):

    IdtTrLockReq: Uint8

    def __init__(self):

        self.IdtTrLockReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
