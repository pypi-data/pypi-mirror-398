from someip_py.codec import *


class IdtDoorLockSts(SomeIpPayload):

    IdtDoorLockSts: Uint8

    def __init__(self):

        self.IdtDoorLockSts = Uint8()
