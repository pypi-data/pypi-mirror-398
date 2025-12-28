from someip_py.codec import *


class IdtPrkgFctVMMModReq(SomeIpPayload):

    IdtPrkgFctVMMModReq: Uint8

    def __init__(self):

        self.IdtPrkgFctVMMModReq = Uint8()
