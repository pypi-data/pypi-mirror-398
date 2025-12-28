from someip_py.codec import *


class IdtTriSt1(SomeIpPayload):

    IdtTriSt1: Uint8

    def __init__(self):

        self.IdtTriSt1 = Uint8()
