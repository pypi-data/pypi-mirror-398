from someip_py.codec import *


class IdtExtLiMode3CtlSts(SomeIpPayload):

    IdtExtLiMode3CtlSts: Uint8

    def __init__(self):

        self.IdtExtLiMode3CtlSts = Uint8()
