from someip_py.codec import *


class IdtPwrModSts(SomeIpPayload):

    IdtPwrModSts: Uint8

    def __init__(self):

        self.IdtPwrModSts = Uint8()
