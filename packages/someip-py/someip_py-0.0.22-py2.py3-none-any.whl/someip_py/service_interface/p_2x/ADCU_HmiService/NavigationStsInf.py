from someip_py.codec import *


class IdtNaviStsSeN(SomeIpPayload):

    IdtNaviStsSeN: Int8

    def __init__(self):

        self.IdtNaviStsSeN = Int8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
