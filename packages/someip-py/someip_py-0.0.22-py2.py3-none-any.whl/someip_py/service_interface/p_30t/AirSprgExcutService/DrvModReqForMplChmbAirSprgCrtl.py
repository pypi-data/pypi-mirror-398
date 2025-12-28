from someip_py.codec import *


class IdtStfnMod(SomeIpPayload):

    IdtStfnMod: Uint8

    def __init__(self):

        self.IdtStfnMod = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
