from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class IdtLineInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    BackLanesSeN: SomeIpDynamicSizeArray[Uint8]

    FrontLansesSeN: SomeIpDynamicSizeArray[Uint8]

    OptimalLanesSeN: SomeIpDynamicSizeArray[Uint8]

    BackExtenLanesSeN: SomeIpDynamicSizeArray[Uint8]

    FrontExtenLanesSeN: SomeIpDynamicSizeArray[Uint8]

    ExtensionLanesSeN: SomeIpDynamicSizeArray[Uint8]

    Pos2DSeN: Pos2D

    SegmentIdxSeN: Uint8

    linkIdxSeN: Uint8

    FrontLaneTypesSeN: SomeIpDynamicSizeArray[Uint8]

    BackLaneTypesSeN: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.BackLanesSeN = SomeIpDynamicSizeArray(Uint8)

        self.FrontLansesSeN = SomeIpDynamicSizeArray(Uint8)

        self.OptimalLanesSeN = SomeIpDynamicSizeArray(Uint8)

        self.BackExtenLanesSeN = SomeIpDynamicSizeArray(Uint8)

        self.FrontExtenLanesSeN = SomeIpDynamicSizeArray(Uint8)

        self.ExtensionLanesSeN = SomeIpDynamicSizeArray(Uint8)

        self.Pos2DSeN = Pos2D()

        self.SegmentIdxSeN = Uint8()

        self.linkIdxSeN = Uint8()

        self.FrontLaneTypesSeN = SomeIpDynamicSizeArray(Uint8)

        self.BackLaneTypesSeN = SomeIpDynamicSizeArray(Uint8)


class IdtLineInfo(SomeIpPayload):

    IdtLineInfo: IdtLineInfoKls

    def __init__(self):

        self.IdtLineInfo = IdtLineInfoKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
