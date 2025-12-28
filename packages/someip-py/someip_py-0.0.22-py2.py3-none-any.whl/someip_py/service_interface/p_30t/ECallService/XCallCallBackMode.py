from someip_py.codec import *


class IdtCallBackMode(SomeIpPayload):

    IdtCallBackMode: Uint8

    def __init__(self):

        self.IdtCallBackMode = Uint8()
