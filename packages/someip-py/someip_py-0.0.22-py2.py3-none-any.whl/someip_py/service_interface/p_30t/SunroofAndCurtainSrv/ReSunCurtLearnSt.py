from someip_py.codec import *


class IdtWMRLearnSts(SomeIpPayload):

    IdtWMRLearnSts: Uint8

    def __init__(self):

        self.IdtWMRLearnSts = Uint8()
