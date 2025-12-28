from someip_py.codec import *


class IdtSingleInhibitReq(SomeIpPayload):

    _include_struct_len = True

    ChrgLidID: Uint8

    InhibitReq: Uint8

    InhbTrigSrc: Uint8

    def __init__(self):

        self.ChrgLidID = Uint8()

        self.InhibitReq = Uint8()

        self.InhbTrigSrc = Uint8()


class IdtInhibitsReq(SomeIpPayload):

    IdtInhibitsReq: SomeIpDynamicSizeArray[IdtSingleInhibitReq]

    def __init__(self):

        self.IdtInhibitsReq = SomeIpDynamicSizeArray(IdtSingleInhibitReq)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
