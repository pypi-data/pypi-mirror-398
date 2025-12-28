from someip_py.codec import *


class IdtAsyALatIndcr(SomeIpPayload):

    IdtAsyALatIndcr: Uint8

    def __init__(self):

        self.IdtAsyALatIndcr = Uint8()
