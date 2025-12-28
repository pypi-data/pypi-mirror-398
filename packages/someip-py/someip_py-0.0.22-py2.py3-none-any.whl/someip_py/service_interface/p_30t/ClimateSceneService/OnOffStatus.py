from someip_py.codec import *


class IdtClimaSceneOnOffStsKls(SomeIpPayload):

    _include_struct_len = True

    WholeOnOff: Uint8

    FirstLeOnOff: Uint8

    FirstRiOnOff: Uint8

    SecLeOnOff: Uint8

    SecRiOnOff: Uint8

    ThrdLeOnOff: Uint8

    ThrdRiOnOff: Uint8

    RearRowOnOff: Uint8

    RearLeftOnOff: Uint8

    RearRightOnOff: Uint8

    ThirdRowOnOff: Uint8

    FrontWholeOnOff: Uint8

    SecRowOnOff: Uint8

    AllOpenOnOff: Uint8

    SpecialFirstRiOnOff: Uint8

    SpecialRearRowOnOff: Uint8

    def __init__(self):

        self.WholeOnOff = Uint8()

        self.FirstLeOnOff = Uint8()

        self.FirstRiOnOff = Uint8()

        self.SecLeOnOff = Uint8()

        self.SecRiOnOff = Uint8()

        self.ThrdLeOnOff = Uint8()

        self.ThrdRiOnOff = Uint8()

        self.RearRowOnOff = Uint8()

        self.RearLeftOnOff = Uint8()

        self.RearRightOnOff = Uint8()

        self.ThirdRowOnOff = Uint8()

        self.FrontWholeOnOff = Uint8()

        self.SecRowOnOff = Uint8()

        self.AllOpenOnOff = Uint8()

        self.SpecialFirstRiOnOff = Uint8()

        self.SpecialRearRowOnOff = Uint8()


class IdtClimaSceneOnOffSts(SomeIpPayload):

    IdtClimaSceneOnOffSts: IdtClimaSceneOnOffStsKls

    def __init__(self):

        self.IdtClimaSceneOnOffSts = IdtClimaSceneOnOffStsKls()
