from someip_py.codec import *


class Object(SomeIpPayload):

    TargetIDSeN: Uint64

    DangerLevelSeN: Uint8

    HeadingSeN: Int16

    CenterPositionXSeN: Int32

    CenterPositionYSeN: Int32

    VelocitySeN: Uint16

    ObjectTypeSeN: Uint8

    SizeXSeN: Uint32

    SizeYSeN: Uint32

    SizeZSeN: Uint32

    TurningLightSeN: Uint8

    MessageLocationSeN: Uint8

    CenterPositionZSeN: Int32

    LiftTurningLightSeN: Uint8

    RightTurningLightSeN: Uint8

    BrakeCarLightSeN: Uint8

    def __init__(self):

        self.TargetIDSeN = Uint64()

        self.DangerLevelSeN = Uint8()

        self.HeadingSeN = Int16()

        self.CenterPositionXSeN = Int32()

        self.CenterPositionYSeN = Int32()

        self.VelocitySeN = Uint16()

        self.ObjectTypeSeN = Uint8()

        self.SizeXSeN = Uint32()

        self.SizeYSeN = Uint32()

        self.SizeZSeN = Uint32()

        self.TurningLightSeN = Uint8()

        self.MessageLocationSeN = Uint8()

        self.CenterPositionZSeN = Int32()

        self.LiftTurningLightSeN = Uint8()

        self.RightTurningLightSeN = Uint8()

        self.BrakeCarLightSeN = Uint8()


class PercepFusionObjs(SomeIpPayload):

    PercepFusionObjs: SomeIpDynamicSizeArray[Object]

    def __init__(self):

        self.PercepFusionObjs = SomeIpDynamicSizeArray(Object)
