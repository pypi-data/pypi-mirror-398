from someip_py.codec import *


class IdtLaneChaSts(SomeIpPayload):

    IdtLaneChaSts: Uint8

    def __init__(self):

        self.IdtLaneChaSts = Uint8()
