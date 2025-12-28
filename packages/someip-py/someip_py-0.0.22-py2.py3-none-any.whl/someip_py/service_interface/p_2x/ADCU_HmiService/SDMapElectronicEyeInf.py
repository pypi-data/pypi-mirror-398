from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class Pos3D(SomeIpPayload):

    LongitudePos3DSeN: Float64

    LatitudePos3DSeN: Float64

    ZPos3DSeN: Float64

    def __init__(self):

        self.LongitudePos3DSeN = Float64()

        self.LatitudePos3DSeN = Float64()

        self.ZPos3DSeN = Float64()


class IdtSubCamera(SomeIpPayload):
    _has_dynamic_size = True

    SubCameraIdSeN: Uint64

    SubTypeSeN: Uint8

    BuswayTimeEnableSeN: Uint8

    PenaltySeN: Uint8

    PrioritySeN: Uint8

    IsNewSeN: Uint8

    IsVariableSpeedSeN: Uint8

    IsMatchSeN: Uint8

    IsSpecialSeN: Uint8

    SubCameraSpeedSeN: SomeIpDynamicSizeArray[Uint16]

    def __init__(self):

        self.SubCameraIdSeN = Uint64()

        self.SubTypeSeN = Uint8()

        self.BuswayTimeEnableSeN = Uint8()

        self.PenaltySeN = Uint8()

        self.PrioritySeN = Uint8()

        self.IsNewSeN = Uint8()

        self.IsVariableSpeedSeN = Uint8()

        self.IsMatchSeN = Uint8()

        self.IsSpecialSeN = Uint8()

        self.SubCameraSpeedSeN = SomeIpDynamicSizeArray(Uint16)


class ElectronicEyeType(SomeIpPayload):
    _has_dynamic_size = True

    CameraIDSeN: Uint64

    Pos2DSeN: Pos2D

    Pos3DSeN: Pos3D

    ElectronicEyeDistanceSeN: Uint32

    SegmentIndexSeN: Uint32

    LinkIndexSeN: Uint32

    DistanceToEndSeN: Uint32

    RoadClassSeN: Uint8

    IsHiddenSeN: Uint8

    NaviSubCamerasSeN: IdtSubCamera

    def __init__(self):

        self.CameraIDSeN = Uint64()

        self.Pos2DSeN = Pos2D()

        self.Pos3DSeN = Pos3D()

        self.ElectronicEyeDistanceSeN = Uint32()

        self.SegmentIndexSeN = Uint32()

        self.LinkIndexSeN = Uint32()

        self.DistanceToEndSeN = Uint32()

        self.RoadClassSeN = Uint8()

        self.IsHiddenSeN = Uint8()

        self.NaviSubCamerasSeN = IdtSubCamera()


class IdtSDMapElectronicEye(SomeIpPayload):

    SDMapElectronicEyeSeN: SomeIpDynamicSizeArray[ElectronicEyeType]

    def __init__(self):

        self.SDMapElectronicEyeSeN = SomeIpDynamicSizeArray(ElectronicEyeType)


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
