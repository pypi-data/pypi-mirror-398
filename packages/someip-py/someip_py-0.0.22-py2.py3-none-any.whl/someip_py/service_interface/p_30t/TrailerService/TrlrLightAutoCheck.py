from someip_py.codec import *


class IdtTrlrLampChkReqFromHmi(SomeIpPayload):

    IdtTrlrLampChkReqFromHmi: Uint8

    def __init__(self):

        self.IdtTrlrLampChkReqFromHmi = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
