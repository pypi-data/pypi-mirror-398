from someip_py.codec import *


class IdtSimCardSts(SomeIpPayload):

    IdtSimCardSts: Uint8

    def __init__(self):

        self.IdtSimCardSts = Uint8()
