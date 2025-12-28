from someip_py.codec import *


class Uni16baseType(SomeIpPayload):

    Uni16baseType: Uint16

    def __init__(self):

        self.Uni16baseType = Uint16()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
