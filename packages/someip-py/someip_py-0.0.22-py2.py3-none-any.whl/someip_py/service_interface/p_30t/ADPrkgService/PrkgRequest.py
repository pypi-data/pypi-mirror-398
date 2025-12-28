from someip_py.codec import *


class IdtPrkgRequestKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Code: Uint8

    Para: SomeIpDynamicSizeArray[Int32]

    def __init__(self):

        self.Code = Uint8()

        self.Para = SomeIpDynamicSizeArray(Int32)


class IdtPrkgRequest(SomeIpPayload):

    IdtPrkgRequest: IdtPrkgRequestKls

    def __init__(self):

        self.IdtPrkgRequest = IdtPrkgRequestKls()


class IdtPrkgRet(SomeIpPayload):

    IdtPrkgRet: Uint8

    def __init__(self):

        self.IdtPrkgRet = Uint8()
