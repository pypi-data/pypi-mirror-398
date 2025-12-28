from someip_py.codec import *


class IdtNodeValue(SomeIpPayload):

    _include_struct_len = True

    NodeID: Uint16

    NodeValue: Uint8

    def __init__(self):

        self.NodeID = Uint16()

        self.NodeValue = Uint8()


class IdtNodeValues(SomeIpPayload):

    IdtNodeValues: SomeIpDynamicSizeArray[IdtNodeValue]

    def __init__(self):

        self.IdtNodeValues = SomeIpDynamicSizeArray(IdtNodeValue)
