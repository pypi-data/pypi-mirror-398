from someip_py.codec import *


class IdtADUO32bit(SomeIpPayload):

    IdtADUO32bit: Uint32

    def __init__(self):

        self.IdtADUO32bit = Uint32()


class IdtADUORet(SomeIpPayload):

    IdtADUORet: Uint8

    def __init__(self):

        self.IdtADUORet = Uint8()
