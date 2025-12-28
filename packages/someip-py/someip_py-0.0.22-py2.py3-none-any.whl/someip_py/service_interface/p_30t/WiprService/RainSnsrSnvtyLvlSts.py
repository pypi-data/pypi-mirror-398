from someip_py.codec import *


class IdtRainSnsrSnvtyLvlStsKls(SomeIpPayload):

    _include_struct_len = True

    RainSnsrLowLvl: Uint8

    RainSnsrHighLvl: Uint8

    def __init__(self):

        self.RainSnsrLowLvl = Uint8()

        self.RainSnsrHighLvl = Uint8()


class IdtRainSnsrSnvtyLvlSts(SomeIpPayload):

    IdtRainSnsrSnvtyLvlSts: IdtRainSnsrSnvtyLvlStsKls

    def __init__(self):

        self.IdtRainSnsrSnvtyLvlSts = IdtRainSnsrSnvtyLvlStsKls()
