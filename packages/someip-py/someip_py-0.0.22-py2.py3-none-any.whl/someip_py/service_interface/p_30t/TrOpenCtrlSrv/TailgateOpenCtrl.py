from someip_py.codec import *


class IdtTailgateOpenCmd(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    TailgateOpenReq: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.TailgateOpenReq = Uint8()


class IdtTailgatesOpenCmd(SomeIpPayload):

    IdtTailgatesOpenCmd: SomeIpDynamicSizeArray[IdtTailgateOpenCmd]

    def __init__(self):

        self.IdtTailgatesOpenCmd = SomeIpDynamicSizeArray(IdtTailgateOpenCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
