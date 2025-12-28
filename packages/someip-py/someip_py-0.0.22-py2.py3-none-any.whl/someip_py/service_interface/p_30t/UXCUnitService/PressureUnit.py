from someip_py.codec import *


class IdtPressureUnit(SomeIpPayload):

    IdtPressureUnit: Uint8

    def __init__(self):

        self.IdtPressureUnit = Uint8()
