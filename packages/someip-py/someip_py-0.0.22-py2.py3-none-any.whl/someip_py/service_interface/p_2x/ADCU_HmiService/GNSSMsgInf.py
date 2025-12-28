from someip_py.codec import *


class IdtGNSSMsgKls(SomeIpPayload):

    GnssLongitudeSeN: Float64

    GnssLatitudeSeN: Float64

    GnssStdLonSeN: Float32

    GnssStdLatSeN: Float32

    GnssTimeSeN: Float64

    GnssTrackTrueAngleSeN: Float64

    GnssAltitudeSeN: Float64

    GnssSpeedHorizontalSeN: Float32

    IMUAccXSeN: Float32

    IMUAccYSeN: Float32

    IMUAccZSeN: Float32

    IMUAngXSeN: Float32

    IMUAngYSeN: Float32

    IMUAngZSeN: Float32

    def __init__(self):

        self.GnssLongitudeSeN = Float64()

        self.GnssLatitudeSeN = Float64()

        self.GnssStdLonSeN = Float32()

        self.GnssStdLatSeN = Float32()

        self.GnssTimeSeN = Float64()

        self.GnssTrackTrueAngleSeN = Float64()

        self.GnssAltitudeSeN = Float64()

        self.GnssSpeedHorizontalSeN = Float32()

        self.IMUAccXSeN = Float32()

        self.IMUAccYSeN = Float32()

        self.IMUAccZSeN = Float32()

        self.IMUAngXSeN = Float32()

        self.IMUAngYSeN = Float32()

        self.IMUAngZSeN = Float32()


class IdtGNSSMsg(SomeIpPayload):

    IdtGNSSMsg: IdtGNSSMsgKls

    def __init__(self):

        self.IdtGNSSMsg = IdtGNSSMsgKls()
