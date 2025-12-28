from someip_py.codec import *


class IdtSubmersionAlrmReq(SomeIpPayload):

    IdtSubmersionAlrmReq: Uint8

    def __init__(self):

        self.IdtSubmersionAlrmReq = Uint8()


class IdtSubmersionAlrmRet(SomeIpPayload):

    IdtSubmersionAlrmRet: Uint8

    def __init__(self):

        self.IdtSubmersionAlrmRet = Uint8()
