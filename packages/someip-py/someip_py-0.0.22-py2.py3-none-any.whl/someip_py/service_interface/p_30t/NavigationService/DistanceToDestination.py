from someip_py.codec import *


class IdtDistanceToDestination(SomeIpPayload):

    IdtDistanceToDestination: Uint32

    def __init__(self):

        self.IdtDistanceToDestination = Uint32()
