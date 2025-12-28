from someip_py.codec import *


class IdtOHCPosition(SomeIpPayload):

    IdtOHCPosition: Uint8

    def __init__(self):

        self.IdtOHCPosition = Uint8()
