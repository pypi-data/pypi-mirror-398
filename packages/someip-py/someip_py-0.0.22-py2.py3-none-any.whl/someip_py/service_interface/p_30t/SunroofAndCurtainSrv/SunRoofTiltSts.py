from someip_py.codec import *


class IdtRoofTiltSts(SomeIpPayload):

    IdtRoofTiltSts: Uint8

    def __init__(self):

        self.IdtRoofTiltSts = Uint8()
