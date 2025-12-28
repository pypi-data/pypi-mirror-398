from someip_py.codec import *


class IdtRainfallAmnt(SomeIpPayload):

    IdtRainfallAmnt: Uint8

    def __init__(self):

        self.IdtRainfallAmnt = Uint8()
