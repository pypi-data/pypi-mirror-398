from someip_py.codec import *


class IdtFavoriteRouteInfoUpdateKls(SomeIpPayload):

    RouteUuid: Uint64

    RouteName: SomeIpDynamicSizeString

    RecommedFlag: Uint8

    DeleteRouteFlag: Uint8

    NaviId: SomeIpDynamicSizeString

    def __init__(self):

        self.RouteUuid = Uint64()

        self.RouteName = SomeIpDynamicSizeString()

        self.RecommedFlag = Uint8()

        self.DeleteRouteFlag = Uint8()

        self.NaviId = SomeIpDynamicSizeString()


class IdtFavoriteRouteInfoUpdate(SomeIpPayload):

    IdtFavoriteRouteInfoUpdate: IdtFavoriteRouteInfoUpdateKls

    def __init__(self):

        self.IdtFavoriteRouteInfoUpdate = IdtFavoriteRouteInfoUpdateKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
