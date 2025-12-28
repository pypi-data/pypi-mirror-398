from someip_py.codec import *


class IdtClimaSetStsKls(SomeIpPayload):

    _include_struct_len = True

    Sync: Uint8

    ECO: Uint8

    SmartOnOff: Uint8

    EvaporatorDry: Uint8

    OverHeat: Uint8

    NaturalWind: Uint8

    def __init__(self):

        self.Sync = Uint8()

        self.ECO = Uint8()

        self.SmartOnOff = Uint8()

        self.EvaporatorDry = Uint8()

        self.OverHeat = Uint8()

        self.NaturalWind = Uint8()


class IdtClimaSetSts(SomeIpPayload):

    IdtClimaSetSts: IdtClimaSetStsKls

    def __init__(self):

        self.IdtClimaSetSts = IdtClimaSetStsKls()
