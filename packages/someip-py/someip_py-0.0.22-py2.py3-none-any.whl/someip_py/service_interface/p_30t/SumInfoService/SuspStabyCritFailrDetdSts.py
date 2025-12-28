from someip_py.codec import *


class IdtSuspStabyCritFailrDetd(SomeIpPayload):

    IdtSuspStabyCritFailrDetd: Uint8

    def __init__(self):

        self.IdtSuspStabyCritFailrDetd = Uint8()
