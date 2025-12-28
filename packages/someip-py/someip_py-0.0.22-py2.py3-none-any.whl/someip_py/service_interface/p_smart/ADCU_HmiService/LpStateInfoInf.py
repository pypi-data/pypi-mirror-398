from someip_py.codec import *


class LPStateKls(SomeIpPayload):

    LPStateSeN: Uint8

    def __init__(self):

        self.LPStateSeN = Uint8()


class LPState(SomeIpPayload):

    LPState: LPStateKls

    def __init__(self):

        self.LPState = LPStateKls()
