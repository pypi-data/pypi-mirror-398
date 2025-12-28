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


class IdtAvoidJamAreaKls(SomeIpPayload):

    BIsVaildSeN: Uint8

    Pos2DSeN: Pos2D

    Pos3DSeN: Pos3D

    EventTypeSeN: Uint32

    SaveTimeSeN: Uint16

    DetourDisSeN: Int32

    JamDistanceSeN: Uint16

    JamStateSeN: Uint16

    def __init__(self):

        self.BIsVaildSeN = Uint8()

        self.Pos2DSeN = Pos2D()

        self.Pos3DSeN = Pos3D()

        self.EventTypeSeN = Uint32()

        self.SaveTimeSeN = Uint16()

        self.DetourDisSeN = Int32()

        self.JamDistanceSeN = Uint16()

        self.JamStateSeN = Uint16()


class IdtAvoidJamArea(SomeIpPayload):

    IdtAvoidJamArea: IdtAvoidJamAreaKls

    def __init__(self):

        self.IdtAvoidJamArea = IdtAvoidJamAreaKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
