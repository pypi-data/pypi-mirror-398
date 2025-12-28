from someip_py.codec import *


class IdtDistanceUnit(SomeIpPayload):

    IdtDistanceUnit: Uint8

    def __init__(self):

        self.IdtDistanceUnit = Uint8()
