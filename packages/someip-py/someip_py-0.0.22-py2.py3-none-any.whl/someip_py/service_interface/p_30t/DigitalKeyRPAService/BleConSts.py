from someip_py.codec import *


class IdtBleConSts(SomeIpPayload):

    IdtBleConSts: Uint8

    def __init__(self):

        self.IdtBleConSts = Uint8()
