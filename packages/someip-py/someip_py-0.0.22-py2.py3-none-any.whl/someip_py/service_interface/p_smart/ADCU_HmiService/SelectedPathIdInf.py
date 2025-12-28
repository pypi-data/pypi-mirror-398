from someip_py.codec import *


class ID32bit(SomeIpPayload):

    ID32bit: Uint32

    def __init__(self):

        self.ID32bit = Uint32()
