from someip_py.codec import *


class IdtSpeedUnit(SomeIpPayload):

    IdtSpeedUnit: Uint8

    def __init__(self):

        self.IdtSpeedUnit = Uint8()
