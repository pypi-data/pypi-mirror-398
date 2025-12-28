from someip_py.codec import *


class IdtADFaultsRequestKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Code: Uint8

    Para: SomeIpDynamicSizeArray[Int32]

    def __init__(self):

        self.Code = Uint8()

        self.Para = SomeIpDynamicSizeArray(Int32)


class IdtADFaultsRequest(SomeIpPayload):

    IdtADFaultsRequest: IdtADFaultsRequestKls

    def __init__(self):

        self.IdtADFaultsRequest = IdtADFaultsRequestKls()


class IdtADFaultsRet(SomeIpPayload):

    IdtADFaultsRet: Uint8

    def __init__(self):

        self.IdtADFaultsRet = Uint8()
