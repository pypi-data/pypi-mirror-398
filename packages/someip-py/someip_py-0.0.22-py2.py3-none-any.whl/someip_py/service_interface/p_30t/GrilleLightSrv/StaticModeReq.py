from someip_py.codec import *


class IdtExLiMode3Req(SomeIpPayload):

    IdtExLiMode3Req: Uint8

    def __init__(self):

        self.IdtExLiMode3Req = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
