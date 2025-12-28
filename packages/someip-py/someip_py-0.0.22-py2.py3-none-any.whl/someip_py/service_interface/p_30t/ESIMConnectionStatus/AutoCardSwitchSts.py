from someip_py.codec import *


class IdtAutoCardSts(SomeIpPayload):

    IdtAutoCardSts: Uint8

    def __init__(self):

        self.IdtAutoCardSts = Uint8()
