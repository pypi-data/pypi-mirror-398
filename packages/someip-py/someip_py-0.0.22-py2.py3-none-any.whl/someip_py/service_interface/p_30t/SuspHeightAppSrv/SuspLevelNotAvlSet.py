from someip_py.codec import *


class IdtLevelAbleStsKls(SomeIpPayload):

    _include_struct_len = True

    NRH: Uint8

    HL2: Uint8

    HL1: Uint8

    LL1: Uint8

    LL2: Uint8

    LL3: Uint8

    HL3: Uint8

    def __init__(self):

        self.NRH = Uint8()

        self.HL2 = Uint8()

        self.HL1 = Uint8()

        self.LL1 = Uint8()

        self.LL2 = Uint8()

        self.LL3 = Uint8()

        self.HL3 = Uint8()


class IdtLevelAbleSts(SomeIpPayload):

    IdtLevelAbleSts: IdtLevelAbleStsKls

    def __init__(self):

        self.IdtLevelAbleSts = IdtLevelAbleStsKls()
