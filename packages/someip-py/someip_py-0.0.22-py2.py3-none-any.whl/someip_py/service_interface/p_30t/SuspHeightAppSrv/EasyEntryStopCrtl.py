from someip_py.codec import *


class IdtOnOffReq(SomeIpPayload):

    IdtOnOffReq: Uint8

    def __init__(self):

        self.IdtOnOffReq = Uint8()
