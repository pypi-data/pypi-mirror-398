from someip_py.codec import *


class IdtDriverModeMsgInfor(SomeIpPayload):

    IdtDriverModeMsgInfor: Uint8

    def __init__(self):

        self.IdtDriverModeMsgInfor = Uint8()
