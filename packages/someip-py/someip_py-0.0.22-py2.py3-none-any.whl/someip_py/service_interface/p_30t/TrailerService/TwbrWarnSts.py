from someip_py.codec import *


class IdtTrlrErr(SomeIpPayload):

    IdtTrlrErr: Uint8

    def __init__(self):

        self.IdtTrlrErr = Uint8()
