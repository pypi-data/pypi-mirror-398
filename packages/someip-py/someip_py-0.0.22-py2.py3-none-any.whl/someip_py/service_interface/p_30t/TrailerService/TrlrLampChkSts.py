from someip_py.codec import *


class IdtTrlrLampChkSts(SomeIpPayload):

    IdtTrlrLampChkSts: Uint8

    def __init__(self):

        self.IdtTrlrLampChkSts = Uint8()
