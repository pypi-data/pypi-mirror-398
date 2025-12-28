from someip_py.codec import *


class IdtExtLiADSCtlSts(SomeIpPayload):

    IdtExtLiADSCtlSts: Uint8

    def __init__(self):

        self.IdtExtLiADSCtlSts = Uint8()
