from someip_py.codec import *


class IdtStfnModforWhlStsKls(SomeIpPayload):

    _include_struct_len = True

    LeFrnt: Uint8

    LeRe: Uint8

    RiFrnt: Uint8

    RiRe: Uint8

    Qf: Uint8

    def __init__(self):

        self.LeFrnt = Uint8()

        self.LeRe = Uint8()

        self.RiFrnt = Uint8()

        self.RiRe = Uint8()

        self.Qf = Uint8()


class IdtStfnModforWhlSts(SomeIpPayload):

    IdtStfnModforWhlSts: IdtStfnModforWhlStsKls

    def __init__(self):

        self.IdtStfnModforWhlSts = IdtStfnModforWhlStsKls()
