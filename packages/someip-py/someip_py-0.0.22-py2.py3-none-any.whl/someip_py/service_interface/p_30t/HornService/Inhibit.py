from someip_py.codec import *


class IdtHornInhibitSrc(SomeIpPayload):

    IdtHornInhibitSrc: Uint8

    def __init__(self):

        self.IdtHornInhibitSrc = Uint8()


class IdtInhibitUninhibit(SomeIpPayload):

    IdtInhibitUninhibit: Uint8

    def __init__(self):

        self.IdtInhibitUninhibit = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
