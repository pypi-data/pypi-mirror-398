from someip_py.codec import *


class IdtAsyALgtIndcr(SomeIpPayload):

    IdtAsyALgtIndcr: Uint8

    def __init__(self):

        self.IdtAsyALgtIndcr = Uint8()
