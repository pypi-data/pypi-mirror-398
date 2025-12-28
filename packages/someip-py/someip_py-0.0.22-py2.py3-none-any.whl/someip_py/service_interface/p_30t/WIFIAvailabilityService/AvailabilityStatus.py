from someip_py.codec import *


class IdtAvailability(SomeIpPayload):

    IdtAvailability: Uint8

    def __init__(self):

        self.IdtAvailability = Uint8()
