from someip_py.codec import *


class IdtChrgLidCtrlReq(SomeIpPayload):

    _include_struct_len = True

    ChrgLidID: Uint8

    ChargeLidCmd: Uint8

    def __init__(self):

        self.ChrgLidID = Uint8()

        self.ChargeLidCmd = Uint8()


class IdtChrgLidsCtrlReq(SomeIpPayload):

    IdtChrgLidsCtrlReq: SomeIpDynamicSizeArray[IdtChrgLidCtrlReq]

    def __init__(self):

        self.IdtChrgLidsCtrlReq = SomeIpDynamicSizeArray(IdtChrgLidCtrlReq)


class IdtChrgLidTrigSrc(SomeIpPayload):

    IdtChrgLidTrigSrc: Uint8

    def __init__(self):

        self.IdtChrgLidTrigSrc = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
