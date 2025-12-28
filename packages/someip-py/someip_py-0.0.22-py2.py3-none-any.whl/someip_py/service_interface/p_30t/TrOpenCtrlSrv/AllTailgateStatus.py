from someip_py.codec import *


class IdtDoorSts(SomeIpPayload):

    IdtDoorSts: Uint8

    def __init__(self):

        self.IdtDoorSts = Uint8()
