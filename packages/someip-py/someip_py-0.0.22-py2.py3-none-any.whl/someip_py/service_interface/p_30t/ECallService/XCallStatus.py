from someip_py.codec import *


class IdtCallStatus(SomeIpPayload):

    IdtCallStatus: Uint8

    def __init__(self):

        self.IdtCallStatus = Uint8()
