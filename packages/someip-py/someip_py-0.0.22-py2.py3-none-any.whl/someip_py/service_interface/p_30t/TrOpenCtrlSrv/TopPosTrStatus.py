from someip_py.codec import *


class IdtTopPosition(SomeIpPayload):

    IdtTopPosition: Uint8

    def __init__(self):

        self.IdtTopPosition = Uint8()
