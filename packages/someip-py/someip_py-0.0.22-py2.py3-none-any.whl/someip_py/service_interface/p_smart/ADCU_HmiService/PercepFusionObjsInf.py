from someip_py.codec import *


class Object(SomeIpPayload):

    TargetIDSeN: Uint64

    DangerLevelSeN: Uint8

    HeadingSeN: Float32

    CenterPositionXSeN: Int16

    CenterPositionYSeN: Int16

    VelocitySeN: Uint16

    ObjectTypeSeN: Uint8

    SizeXSeN: Uint32

    SizeYSeN: Uint32

    SizeZSeN: Uint32

    TurningLightSeN: Uint8

    ObjectTime: Uint64

    BrakeLightSeN: Uint8

    def __init__(self):

        self.TargetIDSeN = Uint64()

        self.DangerLevelSeN = Uint8()

        self.HeadingSeN = Float32()

        self.CenterPositionXSeN = Int16()

        self.CenterPositionYSeN = Int16()

        self.VelocitySeN = Uint16()

        self.ObjectTypeSeN = Uint8()

        self.SizeXSeN = Uint32()

        self.SizeYSeN = Uint32()

        self.SizeZSeN = Uint32()

        self.TurningLightSeN = Uint8()

        self.ObjectTime = Uint64()

        self.BrakeLightSeN = Uint8()


class PercepFusionObjs(SomeIpPayload):

    PercepFusionObjs: SomeIpDynamicSizeArray[Object]

    def __init__(self):

        self.PercepFusionObjs = SomeIpDynamicSizeArray(Object)
