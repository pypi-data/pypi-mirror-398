from someip_py.codec import *


class IdtADCURequestKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Code: Uint8

    Para: SomeIpDynamicSizeArray[Int32]

    def __init__(self):

        self.Code = Uint8()

        self.Para = SomeIpDynamicSizeArray(Int32)


class IdtADCURequest(SomeIpPayload):

    IdtADCURequest: IdtADCURequestKls

    def __init__(self):

        self.IdtADCURequest = IdtADCURequestKls()


class IdtADCURet(SomeIpPayload):

    IdtADCURet: Uint8

    def __init__(self):

        self.IdtADCURet = Uint8()
