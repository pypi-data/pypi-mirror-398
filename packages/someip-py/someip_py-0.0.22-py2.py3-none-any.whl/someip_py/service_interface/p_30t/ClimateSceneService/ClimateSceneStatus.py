from someip_py.codec import *


class IdtClimaApplStsKls(SomeIpPayload):

    _include_struct_len = True

    Off: Uint8

    NormalComfort: Uint8

    MaxDefrst: Uint8

    MaxAC: Uint8

    MaxHeating: Uint8

    SpecificAutoClima: Uint8

    Vent: Uint8

    IntelligentClngSmell: Uint8

    OverHeat: Uint8

    MaxVent: Uint8

    EvaporatorDry: Uint8

    CmptmtHighTempClng: Uint8

    HVACHighTempSterilization: Uint8

    Scene12: Uint8

    Scene13: Uint8

    Scene14: Uint8

    Scene15: Uint8

    def __init__(self):

        self.Off = Uint8()

        self.NormalComfort = Uint8()

        self.MaxDefrst = Uint8()

        self.MaxAC = Uint8()

        self.MaxHeating = Uint8()

        self.SpecificAutoClima = Uint8()

        self.Vent = Uint8()

        self.IntelligentClngSmell = Uint8()

        self.OverHeat = Uint8()

        self.MaxVent = Uint8()

        self.EvaporatorDry = Uint8()

        self.CmptmtHighTempClng = Uint8()

        self.HVACHighTempSterilization = Uint8()

        self.Scene12 = Uint8()

        self.Scene13 = Uint8()

        self.Scene14 = Uint8()

        self.Scene15 = Uint8()


class IdtClimaApplSts(SomeIpPayload):

    IdtClimaApplSts: IdtClimaApplStsKls

    def __init__(self):

        self.IdtClimaApplSts = IdtClimaApplStsKls()
