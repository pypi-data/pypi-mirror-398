from someip_py.codec import *


class CoordinateSys(SomeIpPayload):

    CoordinateXSeN: Int32

    CoordinateYSeN: Int32

    CoordinateZSeN: Int32

    def __init__(self):

        self.CoordinateXSeN = Int32()

        self.CoordinateYSeN = Int32()

        self.CoordinateZSeN = Int32()


class MapBoundary(SomeIpPayload):
    _has_dynamic_size = True

    BoundaryIDSeN: Uint64

    LineTypeSeN: Uint8

    LineMarkingSeN: Uint8

    IDMSeN: Uint8

    BoundaryConfidenceSeN: Float32

    GeometryPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    BoundaryColorSeN: Uint8

    FloorStartSeN: Int8

    FloorEndSeN: Int8

    NavigationTaskOrder: Uint8

    def __init__(self):

        self.BoundaryIDSeN = Uint64()

        self.LineTypeSeN = Uint8()

        self.LineMarkingSeN = Uint8()

        self.IDMSeN = Uint8()

        self.BoundaryConfidenceSeN = Float32()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.BoundaryColorSeN = Uint8()

        self.FloorStartSeN = Int8()

        self.FloorEndSeN = Int8()

        self.NavigationTaskOrder = Uint8()


class MapStopline(SomeIpPayload):
    _has_dynamic_size = True

    StoplineIDSeN: Uint64

    GeometryPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    def __init__(self):

        self.StoplineIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)


class MapCrossWalk(SomeIpPayload):
    _has_dynamic_size = True

    CrossWalkIDSeN: Uint64

    GeometryPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    CrossWalkDirectionSeN: Int32

    def __init__(self):

        self.CrossWalkIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.CrossWalkDirectionSeN = Int32()


class MapRoadMark(SomeIpPayload):
    _has_dynamic_size = True

    RoadmarkIDSeN: Uint64

    RoadmarkTypeSeN: Uint8

    BoundaryBoxSeN: SomeIpDynamicSizeArray[CoordinateSys]

    GeometryPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    RoadMarkDirectionSeN: Int32

    FloorStartSeN: Int8

    FloorEndSeN: Int8

    def __init__(self):

        self.RoadmarkIDSeN = Uint64()

        self.RoadmarkTypeSeN = Uint8()

        self.BoundaryBoxSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.RoadMarkDirectionSeN = Int32()

        self.FloorStartSeN = Int8()

        self.FloorEndSeN = Int8()


class MapLaneInfo(SomeIpPayload):
    _has_dynamic_size = True

    LaneColorSeN: Uint8

    LaneAnimationTypeSeN: Uint8

    AreaTypeSeN: Uint8

    AreaConfidenceSeN: Float32

    LeftBoundarySeN: SomeIpDynamicSizeArray[CoordinateSys]

    RightBoundarySeN: SomeIpDynamicSizeArray[CoordinateSys]

    AreaPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    FloorStartSeN: Int8

    FloorEndSeN: Int8

    def __init__(self):

        self.LaneColorSeN = Uint8()

        self.LaneAnimationTypeSeN = Uint8()

        self.AreaTypeSeN = Uint8()

        self.AreaConfidenceSeN = Float32()

        self.LeftBoundarySeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.RightBoundarySeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.AreaPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.FloorStartSeN = Int8()

        self.FloorEndSeN = Int8()


class MapSlotType(SomeIpPayload):
    _has_dynamic_size = True

    SlotIDSeN: Uint32

    SlotStatusSeN: Uint8

    SlotTypeSeN: Uint8

    SlotPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    BlockPointsSeN: SomeIpDynamicSizeArray[CoordinateSys]

    SlotSelectButtonSeN: Uint8

    FloorStartSeN: Int8

    FloorEndSeN: Int8

    ApaChargeSlotSeN: Uint8

    ApaChargeSlotNum: SomeIpDynamicSizeArray[Int8]

    ApaReqReleaseLockCard: Uint8

    SlotSizeTypeSeN: Uint8

    LockStatusSeN: Uint8

    LockFlagSeN: Uint8

    def __init__(self):

        self.SlotIDSeN = Uint32()

        self.SlotStatusSeN = Uint8()

        self.SlotTypeSeN = Uint8()

        self.SlotPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.BlockPointsSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.SlotSelectButtonSeN = Uint8()

        self.FloorStartSeN = Int8()

        self.FloorEndSeN = Int8()

        self.ApaChargeSlotSeN = Uint8()

        self.ApaChargeSlotNum = SomeIpDynamicSizeArray(Int8)

        self.ApaReqReleaseLockCard = Uint8()

        self.SlotSizeTypeSeN = Uint8()

        self.LockStatusSeN = Uint8()

        self.LockFlagSeN = Uint8()


class SubMap(SomeIpPayload):
    _has_dynamic_size = True

    SubMapIdSeN: Uint64

    FloorSeN: Int8

    MapBoundariesSeN: SomeIpDynamicSizeArray[MapBoundary]

    MapStoplinesSeN: SomeIpDynamicSizeArray[MapStopline]

    MapCrosswalksSeN: SomeIpDynamicSizeArray[MapCrossWalk]

    MapRoadmarksSeN: SomeIpDynamicSizeArray[MapRoadMark]

    MapTargetLaneSeN: MapLaneInfo

    MapRoadSurfaceSeN: SomeIpDynamicSizeArray[MapLaneInfo]

    MapSlotsSeN: SomeIpDynamicSizeArray[MapSlotType]

    def __init__(self):

        self.SubMapIdSeN = Uint64()

        self.FloorSeN = Int8()

        self.MapBoundariesSeN = SomeIpDynamicSizeArray(MapBoundary)

        self.MapStoplinesSeN = SomeIpDynamicSizeArray(MapStopline)

        self.MapCrosswalksSeN = SomeIpDynamicSizeArray(MapCrossWalk)

        self.MapRoadmarksSeN = SomeIpDynamicSizeArray(MapRoadMark)

        self.MapTargetLaneSeN = MapLaneInfo()

        self.MapRoadSurfaceSeN = SomeIpDynamicSizeArray(MapLaneInfo)

        self.MapSlotsSeN = SomeIpDynamicSizeArray(MapSlotType)


class Idt3DMapForAVPKls(SomeIpPayload):
    _has_dynamic_size = True

    MapIdSeN: Uint64

    MapFloorNumSeN: Uint8

    SubMapSeN: SomeIpDynamicSizeArray[SubMap]

    def __init__(self):

        self.MapIdSeN = Uint64()

        self.MapFloorNumSeN = Uint8()

        self.SubMapSeN = SomeIpDynamicSizeArray(SubMap)


class Idt3DMapForAVP(SomeIpPayload):

    Idt3DMapForAVP: Idt3DMapForAVPKls

    def __init__(self):

        self.Idt3DMapForAVP = Idt3DMapForAVPKls()
