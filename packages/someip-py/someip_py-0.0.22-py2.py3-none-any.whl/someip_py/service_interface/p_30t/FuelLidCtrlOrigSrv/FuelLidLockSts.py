from someip_py.codec import *


class IdtFuelLidLockSts(SomeIpPayload):

    IdtFuelLidLockSts: Uint8

    def __init__(self):

        self.IdtFuelLidLockSts = Uint8()
