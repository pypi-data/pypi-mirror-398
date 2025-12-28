from someip_py.codec import *


class IdtWipgOnOffSts(SomeIpPayload):

    IdtWipgOnOffSts: Uint8

    def __init__(self):

        self.IdtWipgOnOffSts = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
