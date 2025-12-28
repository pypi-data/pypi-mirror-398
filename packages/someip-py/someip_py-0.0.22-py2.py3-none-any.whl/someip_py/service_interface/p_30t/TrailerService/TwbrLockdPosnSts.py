from someip_py.codec import *


class IdtLockdPosn(SomeIpPayload):

    IdtLockdPosn: Uint8

    def __init__(self):

        self.IdtLockdPosn = Uint8()
