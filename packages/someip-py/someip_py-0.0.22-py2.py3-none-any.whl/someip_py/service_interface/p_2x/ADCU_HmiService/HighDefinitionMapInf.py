from someip_py.codec import *


class VehiclePoint(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()


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

    def __init__(self):

        self.StoplineIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)


class CrossWalk(SomeIpPayload):
    _has_dynamic_size = True

    CrossWalkIDSeN: Uint64

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    CrossWalkDirectionSeN: Int32

    def __init__(self):

        self.CrossWalkIDSeN = Uint64()

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.CrossWalkDirectionSeN = Int32()


class RoadMark(SomeIpPayload):
    _has_dynamic_size = True

    RoadmarkIDSeN: Uint64

    RoadmarkTypeSeN: Uint8

    BoundaryBoxSeN: SomeIpDynamicSizeArray[VehiclePoint]

    GeometryPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    RoadMarkDirectionSeN: Int32

    def __init__(self):

        self.RoadmarkIDSeN = Uint64()

        self.RoadmarkTypeSeN = Uint8()

        self.BoundaryBoxSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.GeometryPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.RoadMarkDirectionSeN = Int32()


class LaneInfo(SomeIpPayload):
    _has_dynamic_size = True

    LaneColorSeN: Uint8

    AreaTypeSeN: Uint8

    AreaConfidenceSeN: Float32

    LeftBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    RightBoundary: SomeIpDynamicSizeArray[VehiclePoint]

    LaneAreaSeN: SomeIpDynamicSizeArray[VehiclePoint]

    LaneAnimationTypeSeN: Uint8

    def __init__(self):

        self.LaneColorSeN = Uint8()

        self.AreaTypeSeN = Uint8()

        self.AreaConfidenceSeN = Float32()

        self.LeftBoundary = SomeIpDynamicSizeArray(VehiclePoint)

        self.RightBoundary = SomeIpDynamicSizeArray(VehiclePoint)

        self.LaneAreaSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.LaneAnimationTypeSeN = Uint8()


class HighDefinitionMapKls(SomeIpPayload):
    _has_dynamic_size = True

    BoundariesSeN: SomeIpDynamicSizeArray[Boundary]

    StoplinesSeN: SomeIpDynamicSizeArray[Stopline]

    CrosswalksSeN: SomeIpDynamicSizeArray[CrossWalk]

    RoadmarksSeN: SomeIpDynamicSizeArray[RoadMark]

    TargetLaneSeN: LaneInfo

    RoadSurfaceSeN: SomeIpDynamicSizeArray[LaneInfo]

    def __init__(self):

        self.BoundariesSeN = SomeIpDynamicSizeArray(Boundary)

        self.StoplinesSeN = SomeIpDynamicSizeArray(Stopline)

        self.CrosswalksSeN = SomeIpDynamicSizeArray(CrossWalk)

        self.RoadmarksSeN = SomeIpDynamicSizeArray(RoadMark)

        self.TargetLaneSeN = LaneInfo()

        self.RoadSurfaceSeN = SomeIpDynamicSizeArray(LaneInfo)


class HighDefinitionMap(SomeIpPayload):

    HighDefinitionMap: HighDefinitionMapKls

    def __init__(self):

        self.HighDefinitionMap = HighDefinitionMapKls()
