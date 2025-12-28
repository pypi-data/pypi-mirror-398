from someip_py.codec import *


class IdtNavilntervalCameraDynamicKls(SomeIpPayload):
    _has_dynamic_size = True

    RateLimitingsSeN: SomeIpDynamicSizeArray[Uint16]

    DistanceSeN: Uint32

    AverageSpeedSeN: Uint16

    ReasonableSpeedInRemainDistSeN: Uint16

    RemainDistanceSeN: Int32

    def __init__(self):

        self.RateLimitingsSeN = SomeIpDynamicSizeArray(Uint16)

        self.DistanceSeN = Uint32()

        self.AverageSpeedSeN = Uint16()

        self.ReasonableSpeedInRemainDistSeN = Uint16()

        self.RemainDistanceSeN = Int32()


class IdtNavilntervalCameraDynamic(SomeIpPayload):

    IdtNavilntervalCameraDynamic: IdtNavilntervalCameraDynamicKls

    def __init__(self):

        self.IdtNavilntervalCameraDynamic = IdtNavilntervalCameraDynamicKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
