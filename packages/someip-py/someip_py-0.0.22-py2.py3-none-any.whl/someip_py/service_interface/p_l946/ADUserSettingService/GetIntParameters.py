from someip_py.codec import *


class IdtkeyIDs(SomeIpPayload):

    IdtkeyIDs: SomeIpDynamicSizeArray[Uint16]

    def __init__(self):

        self.IdtkeyIDs = SomeIpDynamicSizeArray(Uint16)


class IdtADUSItem(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int16

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int16()


class IdtADUSItems(SomeIpPayload):

    IdtADUSItems: SomeIpDynamicSizeArray[IdtADUSItem]

    def __init__(self):

        self.IdtADUSItems = SomeIpDynamicSizeArray(IdtADUSItem)
