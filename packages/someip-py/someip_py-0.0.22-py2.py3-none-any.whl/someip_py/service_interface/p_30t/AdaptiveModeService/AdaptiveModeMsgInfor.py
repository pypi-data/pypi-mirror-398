from someip_py.codec import *


class IdtAdaptiveModeMsgInfor(SomeIpPayload):

    IdtAdaptiveModeMsgInfor: Uint8

    def __init__(self):

        self.IdtAdaptiveModeMsgInfor = Uint8()
