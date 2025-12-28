from someip_py.codec import *


class IdtSingleSwtStsStruct(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    SwtSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.SwtSts = Uint8()


class IdtTrSwtStsAry(SomeIpPayload):

    IdtTrSwtStsAry: SomeIpDynamicSizeArray[IdtSingleSwtStsStruct]

    def __init__(self):

        self.IdtTrSwtStsAry = SomeIpDynamicSizeArray(IdtSingleSwtStsStruct)
