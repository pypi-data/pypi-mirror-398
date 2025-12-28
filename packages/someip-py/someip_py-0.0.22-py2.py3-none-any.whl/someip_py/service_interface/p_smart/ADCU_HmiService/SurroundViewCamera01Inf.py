from someip_py.codec import *


class DistortionCente(SomeIpPayload):

    DistortionCenteXSeN: Float64

    DistortionCenteYSeN: Float64

    def __init__(self):

        self.DistortionCenteXSeN = Float64()

        self.DistortionCenteYSeN = Float64()


class AffineTransformationCoefficient(SomeIpPayload):

    AffineTransformationCoefficientCSeN: Float64

    AffineTransformationCoefficientDSeN: Float64

    AffineTransformationCoefficientESeN: Float64

    def __init__(self):

        self.AffineTransformationCoefficientCSeN = Float64()

        self.AffineTransformationCoefficientDSeN = Float64()

        self.AffineTransformationCoefficientESeN = Float64()


class ForwardProjectionCoefficient(SomeIpPayload):

    ForwardProjectionCoefficientA0: Float64

    ForwardProjectionCoefficientA1: Float64

    ForwardProjectionCoefficientA2: Float64

    ForwardProjectionCoefficientA3: Float64

    ForwardProjectionCoefficientA4: Float64

    def __init__(self):

        self.ForwardProjectionCoefficientA0 = Float64()

        self.ForwardProjectionCoefficientA1 = Float64()

        self.ForwardProjectionCoefficientA2 = Float64()

        self.ForwardProjectionCoefficientA3 = Float64()

        self.ForwardProjectionCoefficientA4 = Float64()


class InverseProjectionCoefficient(SomeIpPayload):

    InverseProjectionCoefficientP0: Float64

    InverseProjectionCoefficientP1: Float64

    InverseProjectionCoefficientP2: Float64

    InverseProjectionCoefficientP3: Float64

    InverseProjectionCoefficientP4: Float64

    InverseProjectionCoefficientP5: Float64

    InverseProjectionCoefficientP6: Float64

    InverseProjectionCoefficientP7: Float64

    InverseProjectionCoefficientP8: Float64

    InverseProjectionCoefficientP9: Float64

    InverseProjectionCoefficientP10: Float64

    InverseProjectionCoefficientP11: Float64

    InverseProjectionCoefficientP12: Float64

    InverseProjectionCoefficientP13: Float64

    InverseProjectionCoefficientP14: Float64

    InverseProjectionCoefficientP15: Float64

    def __init__(self):

        self.InverseProjectionCoefficientP0 = Float64()

        self.InverseProjectionCoefficientP1 = Float64()

        self.InverseProjectionCoefficientP2 = Float64()

        self.InverseProjectionCoefficientP3 = Float64()

        self.InverseProjectionCoefficientP4 = Float64()

        self.InverseProjectionCoefficientP5 = Float64()

        self.InverseProjectionCoefficientP6 = Float64()

        self.InverseProjectionCoefficientP7 = Float64()

        self.InverseProjectionCoefficientP8 = Float64()

        self.InverseProjectionCoefficientP9 = Float64()

        self.InverseProjectionCoefficientP10 = Float64()

        self.InverseProjectionCoefficientP11 = Float64()

        self.InverseProjectionCoefficientP12 = Float64()

        self.InverseProjectionCoefficientP13 = Float64()

        self.InverseProjectionCoefficientP14 = Float64()

        self.InverseProjectionCoefficientP15 = Float64()


class SurroundViewCamera01para(SomeIpPayload):

    CRCValueSeN: Uint8

    SurroundViewCamera01IDSeN: Uint64

    SerialNumber01SeN: Uint64

    DistortionCenter01SeN: DistortionCente

    AffineTransformationCoefficientSeN: AffineTransformationCoefficient

    ForwardProjectionCoefficientSeN: ForwardProjectionCoefficient

    InverseProjectionCoefficientSeN: InverseProjectionCoefficient

    def __init__(self):

        self.CRCValueSeN = Uint8()

        self.SurroundViewCamera01IDSeN = Uint64()

        self.SerialNumber01SeN = Uint64()

        self.DistortionCenter01SeN = DistortionCente()

        self.AffineTransformationCoefficientSeN = AffineTransformationCoefficient()

        self.ForwardProjectionCoefficientSeN = ForwardProjectionCoefficient()

        self.InverseProjectionCoefficientSeN = InverseProjectionCoefficient()


class SurroundViewCamera01Info(SomeIpPayload):

    SurroundViewCamera01Info: SomeIpDynamicSizeArray[SurroundViewCamera01para]

    def __init__(self):

        self.SurroundViewCamera01Info = SomeIpDynamicSizeArray(SurroundViewCamera01para)
