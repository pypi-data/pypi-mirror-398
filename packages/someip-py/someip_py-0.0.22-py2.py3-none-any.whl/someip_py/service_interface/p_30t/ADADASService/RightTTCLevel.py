from someip_py.codec import *


class IdtDOWTTCLevel(SomeIpPayload):

    IdtDOWTTCLevel: Uint8

    def __init__(self):

        self.IdtDOWTTCLevel = Uint8()
