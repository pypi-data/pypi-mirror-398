from someip_py.codec import *


class IdtSunRoofStopReason(SomeIpPayload):

    IdtSunRoofStopReason: Uint8

    def __init__(self):

        self.IdtSunRoofStopReason = Uint8()
