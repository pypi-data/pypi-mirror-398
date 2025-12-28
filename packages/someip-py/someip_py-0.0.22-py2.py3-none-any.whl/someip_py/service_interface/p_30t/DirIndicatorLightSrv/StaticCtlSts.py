from someip_py.codec import *


class IdtIndcrLiCtlSts(SomeIpPayload):

    IdtIndcrLiCtlSts: Uint8

    def __init__(self):

        self.IdtIndcrLiCtlSts = Uint8()
