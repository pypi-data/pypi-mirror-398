from someip_py.codec import *


class IdtPrkAssiSysFltSts(SomeIpPayload):

    IdtPrkAssiSysFltSts: Uint8

    def __init__(self):

        self.IdtPrkAssiSysFltSts = Uint8()
