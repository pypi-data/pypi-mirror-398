from someip_py.codec import *


class IdtSwtDiagcSts(SomeIpPayload):

    IdtSwtDiagcSts: Uint8

    def __init__(self):

        self.IdtSwtDiagcSts = Uint8()
