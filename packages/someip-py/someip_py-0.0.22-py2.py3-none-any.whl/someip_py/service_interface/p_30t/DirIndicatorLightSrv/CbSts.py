from someip_py.codec import *


class IdtExtLiCtlSts(SomeIpPayload):

    IdtExtLiCtlSts: Uint8

    def __init__(self):

        self.IdtExtLiCtlSts = Uint8()
