from someip_py.codec import *


class IdtLockStatus(SomeIpPayload):

    IdtLockStatus: Uint8

    def __init__(self):

        self.IdtLockStatus = Uint8()
