from someip_py.codec import *


class IdtIndcrSwtDevSts(SomeIpPayload):

    IdtIndcrSwtDevSts: Uint8

    def __init__(self):

        self.IdtIndcrSwtDevSts = Uint8()
