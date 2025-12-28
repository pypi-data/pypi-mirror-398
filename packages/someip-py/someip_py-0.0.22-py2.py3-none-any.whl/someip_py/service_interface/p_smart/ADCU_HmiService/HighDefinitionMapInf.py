from someip_py.codec import *


class VehiclePoint(SomeIpPayload):

    PositionXSeN: Int16

    PositionYSeN: Int16

    def __init__(self):

        self.PositionXSeN = Int16()

        self.PositionYSeN = Int16()


class Boundary(SomeIpPayload):
    _has_dynamic_size = True

    BoundaryIDSeN: Uint64

    LineTypeSeN: Uint8

    LineMarkingSeN: Uint8

    IDMSeN: Uint8

    BoundaryConfidenceSeN: Float32

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    BoundaryColorSeN: Uint8

    def __init__(self):

        self.BoundaryIDSeN = Uint64()

        self.LineTypeSeN = Uint8()

        self.LineMarkingSeN = Uint8()

        self.IDMSeN = Uint8()

        self.BoundaryConfidenceSeN = Float32()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.BoundaryColorSeN = Uint8()


class Stopline(SomeIpPayload):
    _has_dynamic_size = True

    StoplineIDSeN: Uint64

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    StoplineColorSeN: Uint8

    def __init__(self):

        self.StoplineIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.StoplineColorSeN = Uint8()


class CrossWalk(SomeIpPayload):
    _has_dynamic_size = True

    CrossWalkIDSeN: Uint64

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    def __init__(self):

        self.CrossWalkIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)


class RoadMark(SomeIpPayload):
    _has_dynamic_size = True

    RoadmarkIDSeN: Uint64

    RoadmarkTypeSeN: Uint8

    BoundaryBoxSeN: SomeIpDynamicSizeArray[VehiclePoint]

    GeometryPointsSeN: VehiclePoint

    RoadMarkWidthSeN: Uint16

    RoadMarkLengthSeN: Uint16

    RoadMarkHeadingSeN: Float32

    def __init__(self):

        self.RoadmarkIDSeN = Uint64()

        self.RoadmarkTypeSeN = Uint8()

        self.BoundaryBoxSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.GeometryPointsSeN = VehiclePoint()

        self.RoadMarkWidthSeN = Uint16()

        self.RoadMarkLengthSeN = Uint16()

        self.RoadMarkHeadingSeN = Float32()


class LaneInfo(SomeIpPayload):
    _has_dynamic_size = True

    LaneColorSeN: Uint8

    AreaTypeSeN: Uint8

    AreaConfidenceSeN: Float32

    LeftBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    RightBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    LaneAreaSeN: SomeIpDynamicSizeArray[VehiclePoint]

    def __init__(self):

        self.LaneColorSeN = Uint8()

        self.AreaTypeSeN = Uint8()

        self.AreaConfidenceSeN = Float32()

        self.LeftBoundary = SomeIpDynamicSizeArray(VehiclePoint)

        self.RightBoundary = SomeIpDynamicSizeArray(VehiclePoint)

        self.LaneAreaSeN = SomeIpDynamicSizeArray(VehiclePoint)


class LaneInfoBoth(SomeIpPayload):
    _has_dynamic_size = True

    TargetIDBothSeN: Uint64

    LaneColorBothSeN: Uint8

    LeftBothBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    RightBothBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    def __init__(self):

        self.TargetIDBothSeN = Uint64()

        self.LaneColorBothSeN = Uint8()

        self.LeftBothBoundary = SomeIpDynamicSizeArray(VehiclePoint)

        self.RightBothBoundary = SomeIpDynamicSizeArray(VehiclePoint)


class AreaInfo(SomeIpPayload):
    _has_dynamic_size = True

    AreaIDSeN: Uint64

    AreaTypeSeN: Uint8

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    def __init__(self):

        self.AreaIDSeN = Uint64()

        self.AreaTypeSeN = Uint8()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)


class HighDefinitionMapKls(SomeIpPayload):
    _has_dynamic_size = True

    BoundariesSeN: SomeIpDynamicSizeArray[Boundary]

    StoplinesSeN: SomeIpDynamicSizeArray[Stopline]

    CrosswalksSeN: SomeIpDynamicSizeArray[CrossWalk]

    RoadmarksSeN: SomeIpDynamicSizeArray[RoadMark]

    TargetLaneSeN: LaneInfo

    RoadSurfaceSeN: SomeIpDynamicSizeArray[LaneInfo]

    TargetLaneBothSeN: SomeIpDynamicSizeArray[LaneInfoBoth]

    GnssTimeStampSeN: Uint64

    AreaSurfaceSeN: SomeIpDynamicSizeArray[AreaInfo]

    def __init__(self):

        self.BoundariesSeN = SomeIpDynamicSizeArray(Boundary)

        self.StoplinesSeN = SomeIpDynamicSizeArray(Stopline)

        self.CrosswalksSeN = SomeIpDynamicSizeArray(CrossWalk)

        self.RoadmarksSeN = SomeIpDynamicSizeArray(RoadMark)

        self.TargetLaneSeN = LaneInfo()

        self.RoadSurfaceSeN = SomeIpDynamicSizeArray(LaneInfo)

        self.TargetLaneBothSeN = SomeIpDynamicSizeArray(LaneInfoBoth)

        self.GnssTimeStampSeN = Uint64()

        self.AreaSurfaceSeN = SomeIpDynamicSizeArray(AreaInfo)


class HighDefinitionMap(SomeIpPayload):

    HighDefinitionMap: HighDefinitionMapKls

    def __init__(self):

        self.HighDefinitionMap = HighDefinitionMapKls()
