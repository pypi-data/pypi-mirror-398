from someip_py.codec import *


class CommutingRouteSelectionReqType(SomeIpPayload):

    NaviID: SomeIpDynamicSizeString

    RouteUuid: Uint64

    SourceApp: Uint8

    CommutingRouteChecked: Uint8

    CommutingRouteType: Uint8

    Anchored: Uint8

    def __init__(self):

        self.NaviID = SomeIpDynamicSizeString()

        self.RouteUuid = Uint64()

        self.SourceApp = Uint8()

        self.CommutingRouteChecked = Uint8()

        self.CommutingRouteType = Uint8()

        self.Anchored = Uint8()


class IdtCommutingRouteSelectionReq(SomeIpPayload):

    CommutingRouteSelectionReqSeN: SomeIpDynamicSizeArray[
        CommutingRouteSelectionReqType
    ]

    def __init__(self):

        self.CommutingRouteSelectionReqSeN = SomeIpDynamicSizeArray(
            CommutingRouteSelectionReqType
        )


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
