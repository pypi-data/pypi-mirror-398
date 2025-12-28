from someip_py.codec import *


class IdtFaultItem(SomeIpPayload):

    _include_struct_len = True

    UID: Uint32

    Operation: Uint8

    def __init__(self):

        self.UID = Uint32()

        self.Operation = Uint8()


class IdtADAlertFaultInfSts(SomeIpPayload):

    IdtADAlertFaultInfSts: SomeIpDynamicSizeArray[IdtFaultItem]

    def __init__(self):

        self.IdtADAlertFaultInfSts = SomeIpDynamicSizeArray(IdtFaultItem)
