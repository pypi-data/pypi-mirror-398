from someip_py.codec import *


class IdtClimaRunngSts(SomeIpPayload):

    IdtClimaRunngSts: Uint8

    def __init__(self):

        self.IdtClimaRunngSts = Uint8()
