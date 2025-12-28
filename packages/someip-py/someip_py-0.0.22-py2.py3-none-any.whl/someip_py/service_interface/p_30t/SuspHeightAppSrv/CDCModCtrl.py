from someip_py.codec import *


class IdtSuspMod(SomeIpPayload):

    IdtSuspMod: Uint8

    def __init__(self):

        self.IdtSuspMod = Uint8()
