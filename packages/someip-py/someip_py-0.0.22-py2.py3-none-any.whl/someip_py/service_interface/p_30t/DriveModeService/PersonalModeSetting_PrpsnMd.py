from someip_py.codec import *


class IdtPrpsnMdReq(SomeIpPayload):

    IdtPrpsnMdReq: Uint8

    def __init__(self):

        self.IdtPrpsnMdReq = Uint8()
