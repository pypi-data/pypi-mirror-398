from someip_py.codec import *


class Object1(SomeIpPayload):

    TargetIDSeN: Uint64

    DangerLevelSeN: Uint8

    HeadingSeN: Float32

    CenterPositionXSeN1: Int32

    CenterPositionYSeN1: Int32

    VelocitySeN: Uint16

    ObjectTypeSeN: Uint8

    SizeXSeN: Uint32

    SizeYSeN: Uint32

    SizeZSeN: Uint32

    TurningLightSeN: Uint8

    ObjectTime: Uint64

    BrakeLightSeN: Uint8

    CenterPositionZSeN1: Int32

    PitchSeN: Int32

    def __init__(self):

        self.TargetIDSeN = Uint64()

        self.DangerLevelSeN = Uint8()

        self.HeadingSeN = Float32()

        self.CenterPositionXSeN1 = Int32()

        self.CenterPositionYSeN1 = Int32()

        self.VelocitySeN = Uint16()

        self.ObjectTypeSeN = Uint8()

        self.SizeXSeN = Uint32()

        self.SizeYSeN = Uint32()

        self.SizeZSeN = Uint32()

        self.TurningLightSeN = Uint8()

        self.ObjectTime = Uint64()

        self.BrakeLightSeN = Uint8()

        self.CenterPositionZSeN1 = Int32()

        self.PitchSeN = Int32()


class LpPercepFusionObjs(SomeIpPayload):

    LpPercepFusionObjs: SomeIpDynamicSizeArray[Object1]

    def __init__(self):

        self.LpPercepFusionObjs = SomeIpDynamicSizeArray(Object1)
