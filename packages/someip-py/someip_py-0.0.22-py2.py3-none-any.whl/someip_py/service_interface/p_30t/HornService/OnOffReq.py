from someip_py.codec import *


class IdtOnOff(SomeIpPayload):

    IdtOnOff: Uint8

    def __init__(self):

        self.IdtOnOff = Uint8()


class IdtHornReqCategory(SomeIpPayload):

    IdtHornReqCategory: Uint8

    def __init__(self):

        self.IdtHornReqCategory = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
