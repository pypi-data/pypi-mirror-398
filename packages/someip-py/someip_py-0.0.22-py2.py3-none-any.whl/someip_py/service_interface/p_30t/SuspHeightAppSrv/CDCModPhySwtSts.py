from someip_py.codec import *


class IdtSuspstsTxtdriver(SomeIpPayload):

    IdtSuspstsTxtdriver: Uint8

    def __init__(self):

        self.IdtSuspstsTxtdriver = Uint8()
