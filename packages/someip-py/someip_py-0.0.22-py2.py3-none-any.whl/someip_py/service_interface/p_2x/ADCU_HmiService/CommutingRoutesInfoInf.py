from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class RouteType(SomeIpPayload):
    _has_dynamic_size = True

    RouteLinks: SomeIpDynamicSizeArray[Uint64]

    RouteUuid: Uint64

    RouteLength: Uint64

    TravelTime: Uint64

    CreationTime: Uint64

    RecommedFlag: Uint8

    NaviId: SomeIpDynamicSizeString

    QualityInspectionSts: Uint8

    RouteNickName: SomeIpDynamicSizeString

    StartPoint: Pos2D

    StartAdcode: Uint32

    DestPoint: Pos2D

    DestAdcode: Uint32

    ParkingFlag: Uint8

    MrStartPoint: Pos2D

    MrEndPoint: Pos2D

    StartName: SomeIpDynamicSizeString

    DestName: SomeIpDynamicSizeString

    ViaPionts: SomeIpDynamicSizeArray[Pos2D]

    Reason: Uint8

    NavigationDisplayDistpiontPOIID: SomeIpDynamicSizeString

    NavigationDistreqType: Uint8

    NavigationDistpiontPOIID: SomeIpDynamicSizeString

    def __init__(self):

        self.RouteLinks = SomeIpDynamicSizeArray(Uint64)

        self.RouteUuid = Uint64()

        self.RouteLength = Uint64()

        self.TravelTime = Uint64()

        self.CreationTime = Uint64()

        self.RecommedFlag = Uint8()

        self.NaviId = SomeIpDynamicSizeString()

        self.QualityInspectionSts = Uint8()

        self.RouteNickName = SomeIpDynamicSizeString()

        self.StartPoint = Pos2D()

        self.StartAdcode = Uint32()

        self.DestPoint = Pos2D()

        self.DestAdcode = Uint32()

        self.ParkingFlag = Uint8()

        self.MrStartPoint = Pos2D()

        self.MrEndPoint = Pos2D()

        self.StartName = SomeIpDynamicSizeString()

        self.DestName = SomeIpDynamicSizeString()

        self.ViaPionts = SomeIpDynamicSizeArray(Pos2D)

        self.Reason = Uint8()

        self.NavigationDisplayDistpiontPOIID = SomeIpDynamicSizeString()

        self.NavigationDistreqType = Uint8()

        self.NavigationDistpiontPOIID = SomeIpDynamicSizeString()


class IdtCommutingRoutesInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    UserGid: SomeIpDynamicSizeString

    RoutesInfoSeN: SomeIpDynamicSizeArray[RouteType]

    def __init__(self):

        self.UserGid = SomeIpDynamicSizeString()

        self.RoutesInfoSeN = SomeIpDynamicSizeArray(RouteType)


class IdtCommutingRoutesInfo(SomeIpPayload):

    IdtCommutingRoutesInfo: IdtCommutingRoutesInfoKls

    def __init__(self):

        self.IdtCommutingRoutesInfo = IdtCommutingRoutesInfoKls()
