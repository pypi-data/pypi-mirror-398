from someip_py.codec import *


class IdtActvnOfBackgroundLi(SomeIpPayload):

    IdtActvnOfBackgroundLi: Uint8

    def __init__(self):

        self.IdtActvnOfBackgroundLi = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
