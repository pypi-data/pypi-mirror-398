from someip_py.codec import *


class IdtIndcrSts(SomeIpPayload):

    IdtIndcrSts: Uint8

    def __init__(self):

        self.IdtIndcrSts = Uint8()
