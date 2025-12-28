from someip_py.codec import *


class EnvRoadLaneLine(SomeIpPayload):
    _has_dynamic_size = True

    RoadLaneLineid: Uint32

    RoadLaneLineType: Uint8

    RoadLaneLineWidth: Uint32

    RoadLaneLineRole: Uint8

    RoadLaneLineColor: Uint8

    LineCurveType: Uint8

    RoadLaneLineStart: Float64

    RoadLaneLineEnd: Float64

    RoadLaneLineCoeff: SomeIpDynamicSizeArray[Float64]

    def __init__(self):

        self.RoadLaneLineid = Uint32()

        self.RoadLaneLineType = Uint8()

        self.RoadLaneLineWidth = Uint32()

        self.RoadLaneLineRole = Uint8()

        self.RoadLaneLineColor = Uint8()

        self.LineCurveType = Uint8()

        self.RoadLaneLineStart = Float64()

        self.RoadLaneLineEnd = Float64()

        self.RoadLaneLineCoeff = SomeIpDynamicSizeArray(Float64)


class LaneLines(SomeIpPayload):

    LaneLines: SomeIpDynamicSizeArray[EnvRoadLaneLine]

    def __init__(self):

        self.LaneLines = SomeIpDynamicSizeArray(EnvRoadLaneLine)
