from someip_py.codec import *


class IdtTowgAblty(SomeIpPayload):

    IdtTowgAblty: Bool

    def __init__(self):

        self.IdtTowgAblty = Bool()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
