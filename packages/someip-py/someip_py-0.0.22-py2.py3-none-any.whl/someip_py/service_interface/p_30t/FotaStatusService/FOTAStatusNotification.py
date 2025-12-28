from someip_py.codec import *


class IdtOTAstatusDetails(SomeIpPayload):

    _include_struct_len = True

    ActionName: Uint8

    ActionStatus: Bool

    def __init__(self):

        self.ActionName = Uint8()

        self.ActionStatus = Bool()


class IdtOTAStatus(SomeIpPayload):

    IdtOTAStatus: SomeIpDynamicSizeArray[IdtOTAstatusDetails]

    def __init__(self):

        self.IdtOTAStatus = SomeIpDynamicSizeArray(IdtOTAstatusDetails)
