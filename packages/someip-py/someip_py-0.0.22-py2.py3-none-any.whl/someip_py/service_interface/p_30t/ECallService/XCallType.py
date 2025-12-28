from someip_py.codec import *


class IdtCallType(SomeIpPayload):

    IdtCallType: Uint8

    def __init__(self):

        self.IdtCallType = Uint8()
