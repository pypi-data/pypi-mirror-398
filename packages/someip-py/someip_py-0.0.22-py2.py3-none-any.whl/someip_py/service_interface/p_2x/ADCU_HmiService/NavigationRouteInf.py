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


class LatLon(SomeIpPayload):

    LatSeN: Float64

    LonSeN: Float64

    def __init__(self):

        self.LatSeN = Float64()

        self.LonSeN = Float64()


class SlopePoint(SomeIpPayload):

    LonIntSeN: Int32

    LatIntSeN: Int32

    SlopePointAngle: Int16

    SlopePointLength: Int32

    SlopePointHight: Int16

    def __init__(self):

        self.LonIntSeN = Int32()

        self.LatIntSeN = Int32()

        self.SlopePointAngle = Int16()

        self.SlopePointLength = Int32()

        self.SlopePointHight = Int16()


class LatLonInt(SomeIpPayload):

    LonIntSeN: Int32

    LatIntSeN: Int32

    def __init__(self):

        self.LonIntSeN = Int32()

        self.LatIntSeN = Int32()


class LinkInfo(SomeIpPayload):
    _has_dynamic_size = True

    LinkPathID: Uint32

    LinkPathSegmentID: Uint32

    LinkID: Uint32

    RDLength: Int32

    RDName: SomeIpDynamicSizeString

    RDDirection: Uint8

    RDMainAction: Uint8

    RDAssistisAction: Uint16

    RDLinkType: Int16

    RDFormWay: Int16

    RDRoadClass: Int16

    RoadDirection: Uint8

    FreeRoadOrNot: Bool

    OverHeadOrNot: Bool

    HasParallelRoadOrNot: Bool

    HasMultiOutOrNot: Bool

    HasTrafficLightOrNot: Bool

    AtServiceOrNot: Bool

    GetSpeedLimit: Uint16

    GetLaneNum: Uint8

    SlopeInfoStatus: Uint8

    SlopePoints: SomeIpDynamicSizeArray[SlopePoint]

    LinkPoints: SomeIpDynamicSizeArray[LatLonInt]

    LinkTopoIDSeN: Uint64

    OnNaviRouteSeN: Bool

    PredecessorLinkIndexsSeN: SomeIpDynamicSizeArray[Uint32]

    SuccessorLinkIndexsSeN: SomeIpDynamicSizeArray[Uint32]

    def __init__(self):

        self.LinkPathID = Uint32()

        self.LinkPathSegmentID = Uint32()

        self.LinkID = Uint32()

        self.RDLength = Int32()

        self.RDName = SomeIpDynamicSizeString()

        self.RDDirection = Uint8()

        self.RDMainAction = Uint8()

        self.RDAssistisAction = Uint16()

        self.RDLinkType = Int16()

        self.RDFormWay = Int16()

        self.RDRoadClass = Int16()

        self.RoadDirection = Uint8()

        self.FreeRoadOrNot = Bool()

        self.OverHeadOrNot = Bool()

        self.HasParallelRoadOrNot = Bool()

        self.HasMultiOutOrNot = Bool()

        self.HasTrafficLightOrNot = Bool()

        self.AtServiceOrNot = Bool()

        self.GetSpeedLimit = Uint16()

        self.GetLaneNum = Uint8()

        self.SlopeInfoStatus = Uint8()

        self.SlopePoints = SomeIpDynamicSizeArray(SlopePoint)

        self.LinkPoints = SomeIpDynamicSizeArray(LatLonInt)

        self.LinkTopoIDSeN = Uint64()

        self.OnNaviRouteSeN = Bool()

        self.PredecessorLinkIndexsSeN = SomeIpDynamicSizeArray(Uint32)

        self.SuccessorLinkIndexsSeN = SomeIpDynamicSizeArray(Uint32)


class Pos3D(SomeIpPayload):

    LongitudePos3DSeN: Float64

    LatitudePos3DSeN: Float64

    ZPos3DSeN: Float64

    def __init__(self):

        self.LongitudePos3DSeN = Float64()

        self.LatitudePos3DSeN = Float64()

        self.ZPos3DSeN = Float64()


class SegmentInfo(SomeIpPayload):

    RelatedPathID: Int64

    SegmentIndex: Int64

    MainAction: Int32

    AssistantAction: Int32

    def __init__(self):

        self.RelatedPathID = Int64()

        self.SegmentIndex = Int64()

        self.MainAction = Int32()

        self.AssistantAction = Int32()


class NavigationInfo(SomeIpPayload):
    _has_dynamic_size = True

    RouteIDSeN: Uint64

    NaviStatusSeN: Uint8

    RouteDatasSeN: SomeIpDynamicSizeArray[LatLon]

    NavigationInfo: SomeIpDynamicSizeArray[LinkInfo]

    DataGramSumNum: Uint8

    DataGramNum: Uint8

    RouteTraLightsSeN: SomeIpDynamicSizeArray[Pos3D]

    SegmentInfomation: SomeIpDynamicSizeArray[SegmentInfo]

    def __init__(self):

        self.RouteIDSeN = Uint64()

        self.NaviStatusSeN = Uint8()

        self.RouteDatasSeN = SomeIpDynamicSizeArray(LatLon)

        self.NavigationInfo = SomeIpDynamicSizeArray(LinkInfo)

        self.DataGramSumNum = Uint8()

        self.DataGramNum = Uint8()

        self.RouteTraLightsSeN = SomeIpDynamicSizeArray(Pos3D)

        self.SegmentInfomation = SomeIpDynamicSizeArray(SegmentInfo)


class NavigationRouteType(SomeIpPayload):
    _has_dynamic_size = True

    Number: Uint8

    Description: RouteType

    Route: NavigationInfo

    def __init__(self):

        self.Number = Uint8()

        self.Description = RouteType()

        self.Route = NavigationInfo()


class IdtNavigationRoute(SomeIpPayload):

    NavigationRoutSeN: SomeIpDynamicSizeArray[NavigationRouteType]

    def __init__(self):

        self.NavigationRoutSeN = SomeIpDynamicSizeArray(NavigationRouteType)


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
