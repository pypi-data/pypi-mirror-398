from someip_py.codec import *


class IdtBothMirrFoldSts(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrFoldSts: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrFoldSts = Uint8()


class IdtMirrFoldStsAry(SomeIpPayload):

    IdtMirrFoldStsAry: SomeIpDynamicSizeArray[IdtBothMirrFoldSts]

    def __init__(self):

        self.IdtMirrFoldStsAry = SomeIpDynamicSizeArray(IdtBothMirrFoldSts)
