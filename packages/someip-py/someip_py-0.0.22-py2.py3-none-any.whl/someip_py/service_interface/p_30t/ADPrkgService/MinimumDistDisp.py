from someip_py.codec import *


class IdtMinimumDistDispKls(SomeIpPayload):

    _include_struct_len = True

    MinimumDistDispRe: Uint8

    StopReqRe: Uint8

    MinimumDistDispFrnt: Uint8

    StopReqFrnt: Uint8

    def __init__(self):

        self.MinimumDistDispRe = Uint8()

        self.StopReqRe = Uint8()

        self.MinimumDistDispFrnt = Uint8()

        self.StopReqFrnt = Uint8()


class IdtMinimumDistDisp(SomeIpPayload):

    IdtMinimumDistDisp: IdtMinimumDistDispKls

    def __init__(self):

        self.IdtMinimumDistDisp = IdtMinimumDistDispKls()
