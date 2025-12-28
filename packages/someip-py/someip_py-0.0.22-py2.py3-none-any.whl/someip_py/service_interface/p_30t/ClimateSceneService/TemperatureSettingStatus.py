from someip_py.codec import *


class IdtClimaSceneTSetStsKls(SomeIpPayload):

    _include_struct_len = True

    WholeT: Float32

    FirstLeT: Float32

    FirstRiT: Float32

    SecLeT: Float32

    SecRiT: Float32

    ThrdLeT: Float32

    ThrdRiT: Float32

    RearRowT: Float32

    RearLeftT: Float32

    RearRightT: Float32

    ThirdRowT: Float32

    FrontWholeT: Float32

    SecRowT: Float32

    AllOpen: Float32

    SpecialFirstRi: Float32

    SpecialRearRow: Float32

    def __init__(self):

        self.WholeT = Float32()

        self.FirstLeT = Float32()

        self.FirstRiT = Float32()

        self.SecLeT = Float32()

        self.SecRiT = Float32()

        self.ThrdLeT = Float32()

        self.ThrdRiT = Float32()

        self.RearRowT = Float32()

        self.RearLeftT = Float32()

        self.RearRightT = Float32()

        self.ThirdRowT = Float32()

        self.FrontWholeT = Float32()

        self.SecRowT = Float32()

        self.AllOpen = Float32()

        self.SpecialFirstRi = Float32()

        self.SpecialRearRow = Float32()


class IdtClimaSceneTSetSts(SomeIpPayload):

    IdtClimaSceneTSetSts: IdtClimaSceneTSetStsKls

    def __init__(self):

        self.IdtClimaSceneTSetSts = IdtClimaSceneTSetStsKls()
