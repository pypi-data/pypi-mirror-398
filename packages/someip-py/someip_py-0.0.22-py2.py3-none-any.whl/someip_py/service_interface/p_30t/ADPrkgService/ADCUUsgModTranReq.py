from someip_py.codec import *


class IdtADCUUsgModTranReq(SomeIpPayload):

    IdtADCUUsgModTranReq: Uint8

    def __init__(self):

        self.IdtADCUUsgModTranReq = Uint8()
