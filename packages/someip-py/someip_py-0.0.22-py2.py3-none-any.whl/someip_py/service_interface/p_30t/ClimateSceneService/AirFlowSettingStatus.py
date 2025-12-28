from someip_py.codec import *


class IdtClimaSceneFanLvlSetStsKls(SomeIpPayload):

    _include_struct_len = True

    WholeFanLvl: Uint8

    FirstLeFanLvl: Uint8

    FirstRiFanLvl: Uint8

    SecLeFanLvl: Uint8

    SecRiFanLvl: Uint8

    ThrdLeFanLvl: Uint8

    ThrdRiFanLvl: Uint8

    RearRowFanLvl: Uint8

    RearLeftFanLvl: Uint8

    RearRightFanLvl: Uint8

    ThirdRowFanLvl: Uint8

    FrontWholeFanLvl: Uint8

    SecRowFanLvl: Uint8

    AllOpen: Uint8

    SpecialFirstRi: Uint8

    SpecialRearRow: Uint8

    def __init__(self):

        self.WholeFanLvl = Uint8()

        self.FirstLeFanLvl = Uint8()

        self.FirstRiFanLvl = Uint8()

        self.SecLeFanLvl = Uint8()

        self.SecRiFanLvl = Uint8()

        self.ThrdLeFanLvl = Uint8()

        self.ThrdRiFanLvl = Uint8()

        self.RearRowFanLvl = Uint8()

        self.RearLeftFanLvl = Uint8()

        self.RearRightFanLvl = Uint8()

        self.ThirdRowFanLvl = Uint8()

        self.FrontWholeFanLvl = Uint8()

        self.SecRowFanLvl = Uint8()

        self.AllOpen = Uint8()

        self.SpecialFirstRi = Uint8()

        self.SpecialRearRow = Uint8()


class IdtClimaSceneFanLvlSetSts(SomeIpPayload):

    IdtClimaSceneFanLvlSetSts: IdtClimaSceneFanLvlSetStsKls

    def __init__(self):

        self.IdtClimaSceneFanLvlSetSts = IdtClimaSceneFanLvlSetStsKls()
