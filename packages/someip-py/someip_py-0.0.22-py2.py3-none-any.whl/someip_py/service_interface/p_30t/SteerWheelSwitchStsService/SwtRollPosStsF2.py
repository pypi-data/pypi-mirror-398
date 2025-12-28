from someip_py.codec import *


class IdtSwtRollPos(SomeIpPayload):

    IdtSwtRollPos: Uint8

    def __init__(self):

        self.IdtSwtRollPos = Uint8()
