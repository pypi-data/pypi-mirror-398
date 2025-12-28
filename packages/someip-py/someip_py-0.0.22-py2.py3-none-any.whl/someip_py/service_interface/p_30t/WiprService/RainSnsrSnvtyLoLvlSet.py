from someip_py.codec import *


class IdtRainSnsrSnvtyLvl(SomeIpPayload):

    IdtRainSnsrSnvtyLvl: Uint8

    def __init__(self):

        self.IdtRainSnsrSnvtyLvl = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
