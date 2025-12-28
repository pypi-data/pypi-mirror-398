from someip_py.codec import *


class IdtFrntWiprWorkReq(SomeIpPayload):

    IdtFrntWiprWorkReq: Uint8

    def __init__(self):

        self.IdtFrntWiprWorkReq = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
