from someip_py.codec import *


class IdtBothMirrorManAdjSts(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrorManualAdjSts: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrorManualAdjSts = Uint8()


class IdtMirrorManualAdjStsAry(SomeIpPayload):

    IdtMirrorManualAdjStsAry: SomeIpDynamicSizeArray[IdtBothMirrorManAdjSts]

    def __init__(self):

        self.IdtMirrorManualAdjStsAry = SomeIpDynamicSizeArray(IdtBothMirrorManAdjSts)
