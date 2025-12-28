from someip_py.codec import *


class IdtTrlrOnOff(SomeIpPayload):

    IdtTrlrOnOff: Uint8

    def __init__(self):

        self.IdtTrlrOnOff = Uint8()
