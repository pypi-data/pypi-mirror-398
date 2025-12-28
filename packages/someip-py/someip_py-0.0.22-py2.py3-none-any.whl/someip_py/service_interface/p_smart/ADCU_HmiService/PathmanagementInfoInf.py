from someip_py.codec import *


class Pathmanagement(SomeIpPayload):

    CRCValueSeN: Uint8

    PathNumberSeN: Uint32

    PathIDSeN: Uint32

    PathHighlightSeN: Uint8

    LpLongitudeSeN: Float64

    LpLatitudeSeN: Float64

    LpParkNumberSeN: Uint32

    def __init__(self):

        self.CRCValueSeN = Uint8()

        self.PathNumberSeN = Uint32()

        self.PathIDSeN = Uint32()

        self.PathHighlightSeN = Uint8()

        self.LpLongitudeSeN = Float64()

        self.LpLatitudeSeN = Float64()

        self.LpParkNumberSeN = Uint32()


class PathmanagementInfo(SomeIpPayload):

    PathmanagementInfo: SomeIpDynamicSizeArray[Pathmanagement]

    def __init__(self):

        self.PathmanagementInfo = SomeIpDynamicSizeArray(Pathmanagement)
