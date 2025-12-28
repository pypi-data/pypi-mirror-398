from someip_py.codec import *


class IdtWarningLevel(SomeIpPayload):

    IdtWarningLevel: Uint8

    def __init__(self):

        self.IdtWarningLevel = Uint8()
