from someip_py.codec import *


class IdtADTiGapAdjKls(SomeIpPayload):

    TiGapAdjOpTypeSeN: Uint8

    TiGapAdjStepSeN: Uint8

    TiGapAdjValueSeN: Uint8

    def __init__(self):

        self.TiGapAdjOpTypeSeN = Uint8()

        self.TiGapAdjStepSeN = Uint8()

        self.TiGapAdjValueSeN = Uint8()


class IdtADTiGapAdj(SomeIpPayload):

    IdtADTiGapAdj: IdtADTiGapAdjKls

    def __init__(self):

        self.IdtADTiGapAdj = IdtADTiGapAdjKls()


class IdtADTiGapAdjRet(SomeIpPayload):

    IdtADTiGapAdjRet: Uint8

    def __init__(self):

        self.IdtADTiGapAdjRet = Uint8()
