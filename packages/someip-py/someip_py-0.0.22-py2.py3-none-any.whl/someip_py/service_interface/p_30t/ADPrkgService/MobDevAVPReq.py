from someip_py.codec import *


class IdtMobDevAVPReq(SomeIpPayload):

    IdtMobDevAVPReq: Uint8

    def __init__(self):

        self.IdtMobDevAVPReq = Uint8()


class IdtAVPReqRet(SomeIpPayload):

    IdtAVPReqRet: Uint8

    def __init__(self):

        self.IdtAVPReqRet = Uint8()
