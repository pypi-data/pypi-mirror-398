from someip_py.codec import *


class IdtUpdateState(SomeIpPayload):

    IdtUpdateState: Uint8

    def __init__(self):

        self.IdtUpdateState = Uint8()
