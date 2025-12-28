from someip_py.codec import *


class IdtClockUnit(SomeIpPayload):

    IdtClockUnit: Uint8

    def __init__(self):

        self.IdtClockUnit = Uint8()
