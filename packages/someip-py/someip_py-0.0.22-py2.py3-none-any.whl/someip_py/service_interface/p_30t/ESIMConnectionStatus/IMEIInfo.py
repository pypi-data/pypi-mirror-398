from someip_py.codec import *


class IdtSimIMEIInfo(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimIMEIInfo: SomeIpDynamicSizeString

    def __init__(self):

        self.SimNo = Uint8()

        self.SimIMEIInfo = SomeIpDynamicSizeString()


class IdtAllIMEIInfo(SomeIpPayload):

    IdtAllIMEIInfo: SomeIpDynamicSizeArray[IdtSimIMEIInfo]

    def __init__(self):

        self.IdtAllIMEIInfo = SomeIpDynamicSizeArray(IdtSimIMEIInfo)
