from someip_py.codec import *


class IdtExtLiDevSts(SomeIpPayload):

    IdtExtLiDevSts: Uint8

    def __init__(self):

        self.IdtExtLiDevSts = Uint8()
