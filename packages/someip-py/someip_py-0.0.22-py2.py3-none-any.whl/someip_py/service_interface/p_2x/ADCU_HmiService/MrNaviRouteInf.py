from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class ConcidenceLink(SomeIpPayload):

    LinkId: Uint64

    StartPoint: Pos2D

    EndPont: Pos2D

    Length: Uint64

    IsConcidence: Uint8

    def __init__(self):

        self.LinkId = Uint64()

        self.StartPoint = Pos2D()

        self.EndPont = Pos2D()

        self.Length = Uint64()

        self.IsConcidence = Uint8()


class ConcidenceStateType(SomeIpPayload):
    _has_dynamic_size = True

    NaviID: SomeIpDynamicSizeString

    RouteUuid: Uint64

    parkingflag: Uint8

    Concidence: SomeIpDynamicSizeArray[ConcidenceLink]

    IsRoute: Uint8

    Type: Uint8

    IsConcidence: Uint8

    def __init__(self):

        self.NaviID = SomeIpDynamicSizeString()

        self.RouteUuid = Uint64()

        self.parkingflag = Uint8()

        self.Concidence = SomeIpDynamicSizeArray(ConcidenceLink)

        self.IsRoute = Uint8()

        self.Type = Uint8()

        self.IsConcidence = Uint8()


class IdtMrNaviRoute(SomeIpPayload):

    MrNaviRouteSeN: SomeIpDynamicSizeArray[ConcidenceStateType]

    def __init__(self):

        self.MrNaviRouteSeN = SomeIpDynamicSizeArray(ConcidenceStateType)
