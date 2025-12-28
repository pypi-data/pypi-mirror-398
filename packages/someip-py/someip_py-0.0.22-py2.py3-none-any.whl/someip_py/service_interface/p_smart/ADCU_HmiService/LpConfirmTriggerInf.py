from someip_py.codec import *


class Trigger1(SomeIpPayload):

    Trigger1: Uint8

    def __init__(self):

        self.Trigger1 = Uint8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
