from someip_py.codec import *


class IdtPrkgVideoReq(SomeIpPayload):

    IdtPrkgVideoReq: Uint8

    def __init__(self):

        self.IdtPrkgVideoReq = Uint8()
