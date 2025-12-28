from someip_py.codec import *


class IdtADASRequestKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Code: Uint8

    Para: SomeIpDynamicSizeArray[Int32]

    def __init__(self):

        self.Code = Uint8()

        self.Para = SomeIpDynamicSizeArray(Int32)


class IdtADASRequest(SomeIpPayload):

    IdtADASRequest: IdtADASRequestKls

    def __init__(self):

        self.IdtADASRequest = IdtADASRequestKls()


class IdtADASRet(SomeIpPayload):

    IdtADASRet: Uint8

    def __init__(self):

        self.IdtADASRet = Uint8()
