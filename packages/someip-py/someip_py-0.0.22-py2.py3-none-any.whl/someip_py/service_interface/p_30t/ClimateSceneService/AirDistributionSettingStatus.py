from someip_py.codec import *


class IdtClimaSceneAirDistbnSetStsKls(SomeIpPayload):

    _include_struct_len = True

    WholeAirDist: Uint8

    FirstLeAirDist: Uint8

    FirstRiAirDist: Uint8

    SecLeAirDist: Uint8

    SecRiAirDist: Uint8

    ThrdLeAirDist: Uint8

    ThrdRiAirDist: Uint8

    RearRowAirDist: Uint8

    RearLeftAirDist: Uint8

    RearRightAirDist: Uint8

    ThirdRowAirDist: Uint8

    FrontWholeAirDist: Uint8

    SecRowAirDist: Uint8

    AllOpen: Uint8

    SpecialFirstRi: Uint8

    SpecialRearRow: Uint8

    def __init__(self):

        self.WholeAirDist = Uint8()

        self.FirstLeAirDist = Uint8()

        self.FirstRiAirDist = Uint8()

        self.SecLeAirDist = Uint8()

        self.SecRiAirDist = Uint8()

        self.ThrdLeAirDist = Uint8()

        self.ThrdRiAirDist = Uint8()

        self.RearRowAirDist = Uint8()

        self.RearLeftAirDist = Uint8()

        self.RearRightAirDist = Uint8()

        self.ThirdRowAirDist = Uint8()

        self.FrontWholeAirDist = Uint8()

        self.SecRowAirDist = Uint8()

        self.AllOpen = Uint8()

        self.SpecialFirstRi = Uint8()

        self.SpecialRearRow = Uint8()


class IdtClimaSceneAirDistbnSetSts(SomeIpPayload):

    IdtClimaSceneAirDistbnSetSts: IdtClimaSceneAirDistbnSetStsKls

    def __init__(self):

        self.IdtClimaSceneAirDistbnSetSts = IdtClimaSceneAirDistbnSetStsKls()
