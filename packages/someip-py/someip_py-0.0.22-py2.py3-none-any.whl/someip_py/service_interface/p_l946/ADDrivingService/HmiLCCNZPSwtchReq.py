from someip_py.codec import *


class IdtHmiLCCNZPSwtchReq(SomeIpPayload):

    IdtHmiLCCNZPSwtchReq: Uint8

    def __init__(self):

        self.IdtHmiLCCNZPSwtchReq = Uint8()


class IdtLCCNZPSwtchRet(SomeIpPayload):

    IdtLCCNZPSwtchRet: Uint8

    def __init__(self):

        self.IdtLCCNZPSwtchRet = Uint8()
