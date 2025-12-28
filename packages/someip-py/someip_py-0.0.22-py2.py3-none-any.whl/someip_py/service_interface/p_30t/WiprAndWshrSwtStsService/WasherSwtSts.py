from someip_py.codec import *


class IdtWinWshr(SomeIpPayload):

    IdtWinWshr: Uint8

    def __init__(self):

        self.IdtWinWshr = Uint8()
