from someip_py.codec import *


class IdtPrkDisCtrlSts(SomeIpPayload):

    IdtPrkDisCtrlSts: Uint8

    def __init__(self):

        self.IdtPrkDisCtrlSts = Uint8()
