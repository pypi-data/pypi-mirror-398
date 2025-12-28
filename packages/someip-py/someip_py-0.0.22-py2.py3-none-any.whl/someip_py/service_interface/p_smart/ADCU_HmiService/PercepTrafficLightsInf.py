from someip_py.codec import *


class CoordinateSys(SomeIpPayload):

    CoordinateXSeN: Int16

    CoordinateYSeN: Int16

    CoordinateZSeN: Int16

    def __init__(self):

        self.CoordinateXSeN = Int16()

        self.CoordinateYSeN = Int16()

        self.CoordinateZSeN = Int16()


class TrafficLight(SomeIpPayload):
    _has_dynamic_size = True

    TrafficLightIDSeN: Uint64

    BboxSeN: SomeIpDynamicSizeArray[CoordinateSys]

    RedlightSeN: Uint8

    ShapeSeN: Uint8

    CountDownSeN: Uint16

    BlinkSeN: Bool

    UseTLAInfoSeN: Bool

    RollSeN: Int32

    PitchSeN: Int32

    YawSeN: Int32

    def __init__(self):

        self.TrafficLightIDSeN = Uint64()

        self.BboxSeN = SomeIpDynamicSizeArray(CoordinateSys)

        self.RedlightSeN = Uint8()

        self.ShapeSeN = Uint8()

        self.CountDownSeN = Uint16()

        self.BlinkSeN = Bool()

        self.UseTLAInfoSeN = Bool()

        self.RollSeN = Int32()

        self.PitchSeN = Int32()

        self.YawSeN = Int32()


class PercepTrafficLights(SomeIpPayload):

    PercepTrafficLights: SomeIpDynamicSizeArray[TrafficLight]

    def __init__(self):

        self.PercepTrafficLights = SomeIpDynamicSizeArray(TrafficLight)
