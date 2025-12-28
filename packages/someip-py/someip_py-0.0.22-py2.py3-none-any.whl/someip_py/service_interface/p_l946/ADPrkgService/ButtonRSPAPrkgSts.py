from someip_py.codec import *


class IdtButtonRSPAPrkgSts(SomeIpPayload):

    IdtButtonRSPAPrkgSts: Uint8

    def __init__(self):

        self.IdtButtonRSPAPrkgSts = Uint8()
