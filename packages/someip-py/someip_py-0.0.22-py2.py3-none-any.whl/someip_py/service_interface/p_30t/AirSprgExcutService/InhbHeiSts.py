from someip_py.codec import *


class IdtTrueFalseSts(SomeIpPayload):

    IdtTrueFalseSts: Uint8

    def __init__(self):

        self.IdtTrueFalseSts = Uint8()
