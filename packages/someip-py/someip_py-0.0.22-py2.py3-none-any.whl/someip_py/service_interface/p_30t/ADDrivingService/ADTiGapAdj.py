from someip_py.codec import *


class IdtADTiGapAdjKls(SomeIpPayload):

    _include_struct_len = True

    OpType: Uint8

    Step: Uint8

    Value: Uint8

    def __init__(self):

        self.OpType = Uint8()

        self.Step = Uint8()

        self.Value = Uint8()


class IdtADTiGapAdj(SomeIpPayload):

    IdtADTiGapAdj: IdtADTiGapAdjKls

    def __init__(self):

        self.IdtADTiGapAdj = IdtADTiGapAdjKls()


class IdtADTiGapAdjRet(SomeIpPayload):

    IdtADTiGapAdjRet: Uint8

    def __init__(self):

        self.IdtADTiGapAdjRet = Uint8()
