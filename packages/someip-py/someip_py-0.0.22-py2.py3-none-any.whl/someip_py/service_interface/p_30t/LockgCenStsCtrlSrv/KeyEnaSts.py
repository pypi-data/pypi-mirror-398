from someip_py.codec import *


class IdtKeyEnaSts(SomeIpPayload):

    IdtKeyEnaSts: Uint8

    def __init__(self):

        self.IdtKeyEnaSts = Uint8()
