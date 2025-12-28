from someip_py.codec import *


class IdtCallBackSts(SomeIpPayload):

    IdtCallBackSts: Uint16

    def __init__(self):

        self.IdtCallBackSts = Uint16()
