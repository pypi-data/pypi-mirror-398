from someip_py.codec import *


class IdtTrlrPrsntExit(SomeIpPayload):

    IdtTrlrPrsntExit: Uint8

    def __init__(self):

        self.IdtTrlrPrsntExit = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
