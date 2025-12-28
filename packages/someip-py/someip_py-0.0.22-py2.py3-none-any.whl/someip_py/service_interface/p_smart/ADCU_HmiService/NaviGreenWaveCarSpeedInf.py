from someip_py.codec import *


class IdtNaviGreenWaveCarSpeedKls(SomeIpPayload):

    PathIDSeN: Uint64

    GreenCntSeN: Uint8

    MaxSpeedSeN: Uint16

    MinSpeedSeN: Uint16

    LightCountSeN: Uint8

    def __init__(self):

        self.PathIDSeN = Uint64()

        self.GreenCntSeN = Uint8()

        self.MaxSpeedSeN = Uint16()

        self.MinSpeedSeN = Uint16()

        self.LightCountSeN = Uint8()


class IdtNaviGreenWaveCarSpeed(SomeIpPayload):

    IdtNaviGreenWaveCarSpeed: IdtNaviGreenWaveCarSpeedKls

    def __init__(self):

        self.IdtNaviGreenWaveCarSpeed = IdtNaviGreenWaveCarSpeedKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
