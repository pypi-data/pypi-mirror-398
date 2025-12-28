from someip_py.codec import *


class IdtIMSADCUSts(SomeIpPayload):

    IdtIMSADCUSts: Uint8

    def __init__(self):

        self.IdtIMSADCUSts = Uint8()
