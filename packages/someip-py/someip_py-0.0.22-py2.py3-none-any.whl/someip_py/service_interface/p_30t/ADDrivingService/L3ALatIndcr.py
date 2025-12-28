from someip_py.codec import *


class IdtL3ALatIndcr(SomeIpPayload):

    IdtL3ALatIndcr: Uint8

    def __init__(self):

        self.IdtL3ALatIndcr = Uint8()
