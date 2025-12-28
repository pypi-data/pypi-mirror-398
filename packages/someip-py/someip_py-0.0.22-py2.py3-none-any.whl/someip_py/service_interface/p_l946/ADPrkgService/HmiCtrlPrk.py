from someip_py.codec import *


class IdtHmiCtrlPrkReq(SomeIpPayload):

    IdtHmiCtrlPrkReq: Uint8

    def __init__(self):

        self.IdtHmiCtrlPrkReq = Uint8()


class IdtHmiCtrlPrkRet(SomeIpPayload):

    IdtHmiCtrlPrkRet: Uint8

    def __init__(self):

        self.IdtHmiCtrlPrkRet = Uint8()
