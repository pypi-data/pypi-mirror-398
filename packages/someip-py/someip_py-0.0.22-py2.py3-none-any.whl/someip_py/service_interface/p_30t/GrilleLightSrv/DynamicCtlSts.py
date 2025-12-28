from someip_py.codec import *


class IdtExtLiMode6CtlSts(SomeIpPayload):

    IdtExtLiMode6CtlSts: Uint8

    def __init__(self):

        self.IdtExtLiMode6CtlSts = Uint8()
