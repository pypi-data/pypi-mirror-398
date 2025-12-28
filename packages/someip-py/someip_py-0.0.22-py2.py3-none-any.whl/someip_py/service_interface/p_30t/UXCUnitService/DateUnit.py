from someip_py.codec import *


class IdtDateUnit(SomeIpPayload):

    IdtDateUnit: Uint8

    def __init__(self):

        self.IdtDateUnit = Uint8()
