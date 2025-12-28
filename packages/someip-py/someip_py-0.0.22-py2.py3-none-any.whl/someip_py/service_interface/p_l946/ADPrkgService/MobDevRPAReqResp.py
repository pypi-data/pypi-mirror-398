from someip_py.codec import *


class IdtMobDevRPAReqResp(SomeIpPayload):

    IdtMobDevRPAReqResp: Uint8

    def __init__(self):

        self.IdtMobDevRPAReqResp = Uint8()
