from someip_py.codec import *


class IdtFuelLidSts(SomeIpPayload):

    IdtFuelLidSts: Uint8

    def __init__(self):

        self.IdtFuelLidSts = Uint8()
