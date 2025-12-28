from someip_py.codec import *


class IdtTemperatureUnit(SomeIpPayload):

    IdtTemperatureUnit: Uint8

    def __init__(self):

        self.IdtTemperatureUnit = Uint8()
