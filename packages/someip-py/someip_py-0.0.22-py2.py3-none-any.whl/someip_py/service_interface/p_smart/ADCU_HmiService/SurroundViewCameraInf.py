from someip_py.codec import *


class FocalDistance(SomeIpPayload):

    FocalDistanceXSeN: Float64

    FocalDistanceYSeN: Float64

    def __init__(self):

        self.FocalDistanceXSeN = Float64()

        self.FocalDistanceYSeN = Float64()


class DistortionCoefficient(SomeIpPayload):

    DistortionCoefficientK1: Float64

    DistortionCoefficientK2: Float64

    DistortionCoefficientK3: Float64

    DistortionCoefficientK4: Float64

    def __init__(self):

        self.DistortionCoefficientK1 = Float64()

        self.DistortionCoefficientK2 = Float64()

        self.DistortionCoefficientK3 = Float64()

        self.DistortionCoefficientK4 = Float64()


class DistortionCente(SomeIpPayload):

    DistortionCenteXSeN: Float64

    DistortionCenteYSeN: Float64

    def __init__(self):

        self.DistortionCenteXSeN = Float64()

        self.DistortionCenteYSeN = Float64()


class SurroundViewCamerapara(SomeIpPayload):

    CRCValueSeN: Uint8

    SurroundViewCameraIDSeN: Uint64

    SerialNumberSeN: Uint64

    FocalDistanceSeN: FocalDistance

    DistortionCoefficientSeN: DistortionCoefficient

    DistortionCenterSeN: DistortionCente

    def __init__(self):

        self.CRCValueSeN = Uint8()

        self.SurroundViewCameraIDSeN = Uint64()

        self.SerialNumberSeN = Uint64()

        self.FocalDistanceSeN = FocalDistance()

        self.DistortionCoefficientSeN = DistortionCoefficient()

        self.DistortionCenterSeN = DistortionCente()


class SurroundViewCameraInfo(SomeIpPayload):

    SurroundViewCameraInfo: SomeIpDynamicSizeArray[SurroundViewCamerapara]

    def __init__(self):

        self.SurroundViewCameraInfo = SomeIpDynamicSizeArray(SurroundViewCamerapara)
