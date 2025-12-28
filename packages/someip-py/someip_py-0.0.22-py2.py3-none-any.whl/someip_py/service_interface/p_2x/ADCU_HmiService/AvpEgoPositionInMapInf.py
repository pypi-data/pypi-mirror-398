from someip_py.codec import *


class IdtAvpEgoPositionInMapKls(SomeIpPayload):

    PositionXSeN: Float32

    PositionYSeN: Float32

    PositionZSeN: Float32

    OrientationXSeN: Float32

    OrientationYSeN: Float32

    OrientationZSeN: Float32

    OrientationWSeN: Float32

    CurrentFloorLevelSeN: Int8

    FloorStartSeN: Int8

    FloorEndSeN: Int8

    def __init__(self):

        self.PositionXSeN = Float32()

        self.PositionYSeN = Float32()

        self.PositionZSeN = Float32()

        self.OrientationXSeN = Float32()

        self.OrientationYSeN = Float32()

        self.OrientationZSeN = Float32()

        self.OrientationWSeN = Float32()

        self.CurrentFloorLevelSeN = Int8()

        self.FloorStartSeN = Int8()

        self.FloorEndSeN = Int8()


class IdtAvpEgoPositionInMap(SomeIpPayload):

    IdtAvpEgoPositionInMap: IdtAvpEgoPositionInMapKls

    def __init__(self):

        self.IdtAvpEgoPositionInMap = IdtAvpEgoPositionInMapKls()
