from someip_py.codec import *


class CoordinateSys(SomeIpPayload):

    CoordinateXSeN: Int32

    CoordinateYSeN: Int32

    CoordinateZSeN: Int32

    def __init__(self):

        self.CoordinateXSeN = Int32()

        self.CoordinateYSeN = Int32()

        self.CoordinateZSeN = Int32()


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class AVPCollectedDestination(SomeIpPayload):

    CollectedDestinationType: Uint8

    CollectedDestinationSlotId: Uint32

    CollectedDestinationPoint: CoordinateSys

    CollectedDestinationFloorLevel: Int8

    CollectedDestinationPOIID: Uint32

    CollectedDestinationPriority: Uint8

    CollectedParkMapId: Uint64

    CollectedDestinationName: SomeIpDynamicSizeString

    CollectedDestinationLabel: SomeIpDynamicSizeString

    DestinationType: Uint8

    DestinationEditType: Uint8

    GlobalLocation: Pos2D

    def __init__(self):

        self.CollectedDestinationType = Uint8()

        self.CollectedDestinationSlotId = Uint32()

        self.CollectedDestinationPoint = CoordinateSys()

        self.CollectedDestinationFloorLevel = Int8()

        self.CollectedDestinationPOIID = Uint32()

        self.CollectedDestinationPriority = Uint8()

        self.CollectedParkMapId = Uint64()

        self.CollectedDestinationName = SomeIpDynamicSizeString()

        self.CollectedDestinationLabel = SomeIpDynamicSizeString()

        self.DestinationType = Uint8()

        self.DestinationEditType = Uint8()

        self.GlobalLocation = Pos2D()


class AVPCollectedMap(SomeIpPayload):
    _has_dynamic_size = True

    MapId: Uint64

    MapName: SomeIpDynamicSizeString

    DestinationNum: Uint32

    DestinationList: SomeIpDynamicSizeArray[AVPCollectedDestination]

    MapLearningTime: Uint64

    MapType: Uint8

    MapCollectPin: Uint8

    MapStatus: Uint8

    MapErrorCode: Uint8

    def __init__(self):

        self.MapId = Uint64()

        self.MapName = SomeIpDynamicSizeString()

        self.DestinationNum = Uint32()

        self.DestinationList = SomeIpDynamicSizeArray(AVPCollectedDestination)

        self.MapLearningTime = Uint64()

        self.MapType = Uint8()

        self.MapCollectPin = Uint8()

        self.MapStatus = Uint8()

        self.MapErrorCode = Uint8()


class GroupRelatedPoint(SomeIpPayload):

    MapId: Uint32

    DestinationId: Uint32

    def __init__(self):

        self.MapId = Uint32()

        self.DestinationId = Uint32()


class MergeMapGroup(SomeIpPayload):
    _has_dynamic_size = True

    GroupRelatedPointList: SomeIpDynamicSizeArray[GroupRelatedPoint]

    def __init__(self):

        self.GroupRelatedPointList = SomeIpDynamicSizeArray(GroupRelatedPoint)


class IdtAVPMapListInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    MapNumSeN: Uint32

    MapListSeN: SomeIpDynamicSizeArray[AVPCollectedMap]

    LocateMapIdSeN: Uint64

    DestinationListSeN: SomeIpDynamicSizeArray[AVPCollectedDestination]

    MaplistType: Uint8

    MergeMapGroupList: SomeIpDynamicSizeArray[MergeMapGroup]

    def __init__(self):

        self.MapNumSeN = Uint32()

        self.MapListSeN = SomeIpDynamicSizeArray(AVPCollectedMap)

        self.LocateMapIdSeN = Uint64()

        self.DestinationListSeN = SomeIpDynamicSizeArray(AVPCollectedDestination)

        self.MaplistType = Uint8()

        self.MergeMapGroupList = SomeIpDynamicSizeArray(MergeMapGroup)


class IdtAVPMapListInfo(SomeIpPayload):

    IdtAVPMapListInfo: IdtAVPMapListInfoKls

    def __init__(self):

        self.IdtAVPMapListInfo = IdtAVPMapListInfoKls()
