from someip_py.codec import *


class IdtASMPwrSavingFb(SomeIpPayload):

    IdtASMPwrSavingFb: Uint8

    def __init__(self):

        self.IdtASMPwrSavingFb = Uint8()
