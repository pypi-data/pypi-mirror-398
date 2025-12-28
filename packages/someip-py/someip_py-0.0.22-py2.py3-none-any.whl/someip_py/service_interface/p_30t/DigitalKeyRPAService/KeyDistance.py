from someip_py.codec import *


class IdtKeyDistance(SomeIpPayload):

    IdtKeyDistance: Uint16

    def __init__(self):

        self.IdtKeyDistance = Uint16()
