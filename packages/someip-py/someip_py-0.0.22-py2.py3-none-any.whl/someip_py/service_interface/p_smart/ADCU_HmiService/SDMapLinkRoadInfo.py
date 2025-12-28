from someip_py.codec import *


class IdtSDMapLinkRoadKls(SomeIpPayload):

    CurrRoadNameNoNavSeN: SomeIpDynamicSizeString

    RoadLevelNoNavSeN: Int32

    CurrLinkID: Uint64

    def __init__(self):

        self.CurrRoadNameNoNavSeN = SomeIpDynamicSizeString()

        self.RoadLevelNoNavSeN = Int32()

        self.CurrLinkID = Uint64()


class IdtSDMapLinkRoad(SomeIpPayload):

    IdtSDMapLinkRoad: IdtSDMapLinkRoadKls

    def __init__(self):

        self.IdtSDMapLinkRoad = IdtSDMapLinkRoadKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
