from someip_py.codec import *


class IdtHmiActiveADCUReq(SomeIpPayload):

    IdtHmiActiveADCUReq: Uint8

    def __init__(self):

        self.IdtHmiActiveADCUReq = Uint8()


class IdtHmiActiveADCURet(SomeIpPayload):

    IdtHmiActiveADCURet: Uint8

    def __init__(self):

        self.IdtHmiActiveADCURet = Uint8()
