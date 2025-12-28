from someip_py.codec import *


class IdtTypeToDestination(SomeIpPayload):

    IdtTypeToDestination: Uint8

    def __init__(self):

        self.IdtTypeToDestination = Uint8()
