from someip_py.codec import *


class IdtReWiprWorkReq(SomeIpPayload):

    IdtReWiprWorkReq: Uint8

    def __init__(self):

        self.IdtReWiprWorkReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
