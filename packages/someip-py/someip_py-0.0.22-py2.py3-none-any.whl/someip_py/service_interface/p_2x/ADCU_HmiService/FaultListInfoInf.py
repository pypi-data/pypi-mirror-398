from someip_py.codec import *


class FaultItem(SomeIpPayload):

    UID: Uint32

    Operation: Uint8

    def __init__(self):

        self.UID = Uint32()

        self.Operation = Uint8()


class FaultListInfo(SomeIpPayload):

    FaultListInfo: SomeIpDynamicSizeArray[FaultItem]

    def __init__(self):

        self.FaultListInfo = SomeIpDynamicSizeArray(FaultItem)
