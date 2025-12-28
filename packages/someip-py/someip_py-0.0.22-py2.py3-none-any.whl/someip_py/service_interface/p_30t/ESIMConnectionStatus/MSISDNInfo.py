from someip_py.codec import *


class IdtSimMSISDNInfo(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimMSISDNInfo: SomeIpDynamicSizeString

    def __init__(self):

        self.SimNo = Uint8()

        self.SimMSISDNInfo = SomeIpDynamicSizeString()


class IdtAllMSISDNInfo(SomeIpPayload):

    IdtAllMSISDNInfo: SomeIpDynamicSizeArray[IdtSimMSISDNInfo]

    def __init__(self):

        self.IdtAllMSISDNInfo = SomeIpDynamicSizeArray(IdtSimMSISDNInfo)
