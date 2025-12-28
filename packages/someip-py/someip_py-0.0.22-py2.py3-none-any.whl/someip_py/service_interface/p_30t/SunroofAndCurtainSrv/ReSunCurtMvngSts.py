from someip_py.codec import *


class IdtWinMovSts(SomeIpPayload):

    IdtWinMovSts: Uint8

    def __init__(self):

        self.IdtWinMovSts = Uint8()
