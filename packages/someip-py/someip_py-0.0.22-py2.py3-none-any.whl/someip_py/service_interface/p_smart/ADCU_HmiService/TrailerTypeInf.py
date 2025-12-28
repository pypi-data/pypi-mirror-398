from someip_py.codec import *


class TrailerTypeInfoKls(SomeIpPayload):

    TrailerTypeSeN: Uint8

    def __init__(self):

        self.TrailerTypeSeN = Uint8()


class TrailerTypeInfo(SomeIpPayload):

    TrailerTypeInfo: TrailerTypeInfoKls

    def __init__(self):

        self.TrailerTypeInfo = TrailerTypeInfoKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
