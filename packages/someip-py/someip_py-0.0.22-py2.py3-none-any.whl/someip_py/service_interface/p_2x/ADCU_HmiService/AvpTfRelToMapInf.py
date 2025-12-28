from someip_py.codec import *


class IdtAvpTfRelToMapKls(SomeIpPayload):

    PositionXSeN: Float32

    PositionYSeN: Float32

    PositionZSeN: Float32

    OrientationXSeN: Float32

    OrientationYSeN: Float32

    OrientationZSeN: Float32

    OrientationWSeN: Float32

    def __init__(self):

        self.PositionXSeN = Float32()

        self.PositionYSeN = Float32()

        self.PositionZSeN = Float32()

        self.OrientationXSeN = Float32()

        self.OrientationYSeN = Float32()

        self.OrientationZSeN = Float32()

        self.OrientationWSeN = Float32()


class IdtAvpTfRelToMap(SomeIpPayload):

    IdtAvpTfRelToMap: IdtAvpTfRelToMapKls

    def __init__(self):

        self.IdtAvpTfRelToMap = IdtAvpTfRelToMapKls()
