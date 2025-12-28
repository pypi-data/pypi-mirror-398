from someip_py.codec import *


class IdtExtrLiStsKls(SomeIpPayload):

    _include_struct_len = True

    HiBeam: Uint8

    LoBeam: Uint8

    DBL: Uint8

    AFS: Uint8

    AHL: Uint8

    AHBC: Uint8

    PosLiFrnt: Uint8

    PosLiRe: Uint8

    Flash: Uint8

    TurnlndrRi: Uint8

    TurnlndrLe: Uint8

    StopLi: Uint8

    FrntFog: Uint8

    ReFog: Uint8

    DRL: Uint8

    ReverseLi: Uint8

    HWL: Uint8

    CornrgLi: Uint8

    HomeSafe: Uint8

    Approach: Uint8

    Welcome: Uint8

    Goodbye: Uint8

    LtgShow: Uint8

    AllWL: Uint8

    def __init__(self):

        self.HiBeam = Uint8()

        self.LoBeam = Uint8()

        self.DBL = Uint8()

        self.AFS = Uint8()

        self.AHL = Uint8()

        self.AHBC = Uint8()

        self.PosLiFrnt = Uint8()

        self.PosLiRe = Uint8()

        self.Flash = Uint8()

        self.TurnlndrRi = Uint8()

        self.TurnlndrLe = Uint8()

        self.StopLi = Uint8()

        self.FrntFog = Uint8()

        self.ReFog = Uint8()

        self.DRL = Uint8()

        self.ReverseLi = Uint8()

        self.HWL = Uint8()

        self.CornrgLi = Uint8()

        self.HomeSafe = Uint8()

        self.Approach = Uint8()

        self.Welcome = Uint8()

        self.Goodbye = Uint8()

        self.LtgShow = Uint8()

        self.AllWL = Uint8()


class IdtExtrLiSts(SomeIpPayload):

    IdtExtrLiSts: IdtExtrLiStsKls

    def __init__(self):

        self.IdtExtrLiSts = IdtExtrLiStsKls()
