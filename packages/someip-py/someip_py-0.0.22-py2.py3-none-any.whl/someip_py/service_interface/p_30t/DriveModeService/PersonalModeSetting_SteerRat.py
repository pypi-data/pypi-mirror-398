from someip_py.codec import *


class IdtSteerRatReq(SomeIpPayload):

    IdtSteerRatReq: Uint8

    def __init__(self):

        self.IdtSteerRatReq = Uint8()
