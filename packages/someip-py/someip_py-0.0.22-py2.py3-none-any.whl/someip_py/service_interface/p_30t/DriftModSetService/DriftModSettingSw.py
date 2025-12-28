from someip_py.codec import *


class IdtDriftModSettingSw(SomeIpPayload):

    IdtDriftModSettingSw: Uint8

    def __init__(self):

        self.IdtDriftModSettingSw = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
