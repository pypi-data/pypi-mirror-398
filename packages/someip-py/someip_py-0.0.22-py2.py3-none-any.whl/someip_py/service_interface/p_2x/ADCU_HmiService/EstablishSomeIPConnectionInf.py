from someip_py.codec import *


class BaseUint8(SomeIpPayload):

    BaseUint8: Uint8

    def __init__(self):

        self.BaseUint8 = Uint8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
