from someip_py.codec import *


class IdtNodeIntValue(SomeIpPayload):

    IdtNodeIntValue: Uint16

    def __init__(self):

        self.IdtNodeIntValue = Uint16()


class IdtNodeParameterValue(SomeIpPayload):

    IdtNodeParameterValue: Uint8

    def __init__(self):

        self.IdtNodeParameterValue = Uint8()
