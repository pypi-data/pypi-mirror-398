from someip_py.codec import *


class IdtSimIMSIInfo(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimIMSIInfo: SomeIpDynamicSizeString

    def __init__(self):

        self.SimNo = Uint8()

        self.SimIMSIInfo = SomeIpDynamicSizeString()


class IdtAllIMSIInfo(SomeIpPayload):

    IdtAllIMSIInfo: SomeIpDynamicSizeArray[IdtSimIMSIInfo]

    def __init__(self):

        self.IdtAllIMSIInfo = SomeIpDynamicSizeArray(IdtSimIMSIInfo)
