from someip_py.codec import *


class IdtSwtRollDir(SomeIpPayload):

    IdtSwtRollDir: Uint8

    def __init__(self):

        self.IdtSwtRollDir = Uint8()
