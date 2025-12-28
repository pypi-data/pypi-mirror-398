from someip_py.codec import *


class IdtGuidanceStatusUpdateKls(SomeIpPayload):

    GuidanceStatus: Uint8

    ParentRouteUuid: Uint64

    RouteUuid: Uint64

    ReasonCode: Uint8

    MemoryRouteFlag: Uint8

    StraightDist: Uint32

    MileageDist: Uint32

    NaviId: SomeIpDynamicSizeString

    GuidanceStatusType: Uint8

    def __init__(self):

        self.GuidanceStatus = Uint8()

        self.ParentRouteUuid = Uint64()

        self.RouteUuid = Uint64()

        self.ReasonCode = Uint8()

        self.MemoryRouteFlag = Uint8()

        self.StraightDist = Uint32()

        self.MileageDist = Uint32()

        self.NaviId = SomeIpDynamicSizeString()

        self.GuidanceStatusType = Uint8()


class IdtGuidanceStatusUpdate(SomeIpPayload):

    IdtGuidanceStatusUpdate: IdtGuidanceStatusUpdateKls

    def __init__(self):

        self.IdtGuidanceStatusUpdate = IdtGuidanceStatusUpdateKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
