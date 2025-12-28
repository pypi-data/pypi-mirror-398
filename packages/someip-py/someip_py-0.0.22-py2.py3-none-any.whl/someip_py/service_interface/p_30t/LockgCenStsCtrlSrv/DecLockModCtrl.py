from someip_py.codec import *


class IdtDecLockModReq(SomeIpPayload):

    IdtDecLockModReq: Uint8

    def __init__(self):

        self.IdtDecLockModReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
