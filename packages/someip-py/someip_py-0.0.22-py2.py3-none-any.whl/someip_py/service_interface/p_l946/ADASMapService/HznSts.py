from someip_py.codec import *


class IdtHznSts(SomeIpPayload):

    IdtHznSts: Uint8

    def __init__(self):

        self.IdtHznSts = Uint8()
