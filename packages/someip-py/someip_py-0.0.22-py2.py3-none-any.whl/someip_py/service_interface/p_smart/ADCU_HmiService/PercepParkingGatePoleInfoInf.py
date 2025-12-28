from someip_py.codec import *


class PercepParkingGatePole(SomeIpPayload):

    ParkingGatePoleIDSeN: Uint64

    HeadingSeN: Float32

    CenterPositionXSeN: Int16

    CenterPositionYSeN: Int16

    CenterPositionXSeN1: Int32

    CenterPositionYSeN1: Int32

    CenterPositionZSeN1: Int32

    PitchSeN: Int32

    ParkingGatePoleTypeSeN: Uint8

    def __init__(self):

        self.ParkingGatePoleIDSeN = Uint64()

        self.HeadingSeN = Float32()

        self.CenterPositionXSeN = Int16()

        self.CenterPositionYSeN = Int16()

        self.CenterPositionXSeN1 = Int32()

        self.CenterPositionYSeN1 = Int32()

        self.CenterPositionZSeN1 = Int32()

        self.PitchSeN = Int32()

        self.ParkingGatePoleTypeSeN = Uint8()


class PercepParkingGatePoleInfo(SomeIpPayload):

    PercepParkingGatePoleInfo: SomeIpDynamicSizeArray[PercepParkingGatePole]

    def __init__(self):

        self.PercepParkingGatePoleInfo = SomeIpDynamicSizeArray(PercepParkingGatePole)
