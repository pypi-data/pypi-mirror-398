from someip_py.codec import *


class IdtTailgateBoolStatus(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    Status: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.Status = Uint8()


class IdtTailgatesBoolStatus(SomeIpPayload):

    IdtTailgatesBoolStatus: SomeIpDynamicSizeArray[IdtTailgateBoolStatus]

    def __init__(self):

        self.IdtTailgatesBoolStatus = SomeIpDynamicSizeArray(IdtTailgateBoolStatus)
