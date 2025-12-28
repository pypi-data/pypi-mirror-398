from someip_py.codec import *


class IdtBoolStatus(SomeIpPayload):

    IdtBoolStatus: Uint8

    def __init__(self):

        self.IdtBoolStatus = Uint8()
