from someip_py.codec import *


class IdtASMPwrSavingPreCdnSts(SomeIpPayload):

    IdtASMPwrSavingPreCdnSts: Uint8

    def __init__(self):

        self.IdtASMPwrSavingPreCdnSts = Uint8()
