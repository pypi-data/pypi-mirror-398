from someip_py.codec import *


class AbsoluteLocalizationKls(SomeIpPayload):

    LongitudeSeN: Float64

    LatitudeSeN: Float64

    AltitudeSeN: Float64

    YawEnuSeN: Float64

    PitchEnuSeN: Float64

    RollEnuSeN: Float64

    VelocitySeN: Float32

    InsVelocityEastSeN: Float32

    InsVelocityNorthSeN: Float32

    InsVelocityUpSeN: Float32

    GnssTimeStampSeN: Uint64

    INSinfiNSPreciousLvlSeN: Uint8

    def __init__(self):

        self.LongitudeSeN = Float64()

        self.LatitudeSeN = Float64()

        self.AltitudeSeN = Float64()

        self.YawEnuSeN = Float64()

        self.PitchEnuSeN = Float64()

        self.RollEnuSeN = Float64()

        self.VelocitySeN = Float32()

        self.InsVelocityEastSeN = Float32()

        self.InsVelocityNorthSeN = Float32()

        self.InsVelocityUpSeN = Float32()

        self.GnssTimeStampSeN = Uint64()

        self.INSinfiNSPreciousLvlSeN = Uint8()


class AbsoluteLocalization(SomeIpPayload):

    AbsoluteLocalization: AbsoluteLocalizationKls

    def __init__(self):

        self.AbsoluteLocalization = AbsoluteLocalizationKls()
