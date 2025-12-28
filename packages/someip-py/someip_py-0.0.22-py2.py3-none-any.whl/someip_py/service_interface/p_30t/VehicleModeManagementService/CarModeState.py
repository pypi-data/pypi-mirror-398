from someip_py.codec import *


class IdtCarModSts(SomeIpPayload):

    IdtCarModSts: Uint8

    def __init__(self):

        self.IdtCarModSts = Uint8()
