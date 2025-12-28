from someip_py.codec import *


class IdtReWshrAvlSts(SomeIpPayload):

    IdtReWshrAvlSts: Uint8

    def __init__(self):

        self.IdtReWshrAvlSts = Uint8()
