from someip_py.codec import *


class IdtHornStatus(SomeIpPayload):

    IdtHornStatus: Uint8

    def __init__(self):

        self.IdtHornStatus = Uint8()
