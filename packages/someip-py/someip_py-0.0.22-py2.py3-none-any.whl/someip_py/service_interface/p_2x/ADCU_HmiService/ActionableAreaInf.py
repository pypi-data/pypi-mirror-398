from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class IdtActionableAreaKls(SomeIpPayload):
    _has_dynamic_size = True

    IDSeN: Uint64

    TypeSeN: Uint8

    FreeSpaceSeN: SomeIpDynamicSizeArray[Pos2D]

    def __init__(self):

        self.IDSeN = Uint64()

        self.TypeSeN = Uint8()

        self.FreeSpaceSeN = SomeIpDynamicSizeArray(Pos2D)


class IdtActionableArea(SomeIpPayload):

    IdtActionableArea: IdtActionableAreaKls

    def __init__(self):

        self.IdtActionableArea = IdtActionableAreaKls()
