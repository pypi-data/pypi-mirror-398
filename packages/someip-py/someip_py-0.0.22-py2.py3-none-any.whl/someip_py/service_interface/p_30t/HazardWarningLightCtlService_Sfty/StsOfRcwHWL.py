from someip_py.codec import *


class IdtRcwHWLSts(SomeIpPayload):

    IdtRcwHWLSts: Uint8

    def __init__(self):

        self.IdtRcwHWLSts = Uint8()
