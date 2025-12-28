from someip_py.codec import *


class IdtBothMirrDwnSts(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrDwnSts: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrDwnSts = Uint8()


class IdtMirrDwnStsAry(SomeIpPayload):

    IdtMirrDwnStsAry: SomeIpDynamicSizeArray[IdtBothMirrDwnSts]

    def __init__(self):

        self.IdtMirrDwnStsAry = SomeIpDynamicSizeArray(IdtBothMirrDwnSts)
