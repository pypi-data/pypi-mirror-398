from someip_py.codec import *


class Trigger(SomeIpPayload):

    Trigger: Uint8

    def __init__(self):

        self.Trigger = Uint8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
