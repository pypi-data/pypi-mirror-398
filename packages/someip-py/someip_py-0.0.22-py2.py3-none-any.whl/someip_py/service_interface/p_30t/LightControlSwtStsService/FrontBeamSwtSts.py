from someip_py.codec import *


class IdtSwtBeamHi(SomeIpPayload):

    IdtSwtBeamHi: Uint8

    def __init__(self):

        self.IdtSwtBeamHi = Uint8()
