from someip_py.codec import *


class IdtReWipr(SomeIpPayload):

    IdtReWipr: Uint8

    def __init__(self):

        self.IdtReWipr = Uint8()
