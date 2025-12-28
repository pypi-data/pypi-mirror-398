from someip_py.codec import *


class IdtWiprSrvModReq(SomeIpPayload):

    IdtWiprSrvModReq: Uint8

    def __init__(self):

        self.IdtWiprSrvModReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
