from someip_py.codec import *


class FaultListInfo(SomeIpPayload):

    FaultListInfo: SomeIpDynamicSizeArray[Uint32]

    def __init__(self):

        self.FaultListInfo = SomeIpDynamicSizeArray(Uint32)
