from someip_py.codec import *


class IdtWipgCritSts(SomeIpPayload):

    IdtWipgCritSts: Uint8

    def __init__(self):

        self.IdtWipgCritSts = Uint8()
