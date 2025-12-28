from someip_py.codec import *


class IdtHornInhibitSts(SomeIpPayload):

    IdtHornInhibitSts: Uint8

    def __init__(self):

        self.IdtHornInhibitSts = Uint8()
