from someip_py.codec import *


class Pos3D(SomeIpPayload):

    LongitudePos3DSeN: Float64

    LatitudePos3DSeN: Float64

    ZPos3DSeN: Float64

    def __init__(self):

        self.LongitudePos3DSeN = Float64()

        self.LatitudePos3DSeN = Float64()

        self.ZPos3DSeN = Float64()


class IdtTrafficLightStatusKls(SomeIpPayload):
    _has_dynamic_size = True

    CrossManeuverIDSeN: Uint8

    TrafficLightTimeSeN: Uint16

    TrafficLightStatusSeN: Uint8

    WaitRountCountSeN: Uint8

    TrafficLightIDSeN: Uint64

    Pos3DSeN: SomeIpDynamicSizeArray[Pos3D]

    def __init__(self):

        self.CrossManeuverIDSeN = Uint8()

        self.TrafficLightTimeSeN = Uint16()

        self.TrafficLightStatusSeN = Uint8()

        self.WaitRountCountSeN = Uint8()

        self.TrafficLightIDSeN = Uint64()

        self.Pos3DSeN = SomeIpDynamicSizeArray(Pos3D)


class IdtTrafficLightStatus(SomeIpPayload):

    IdtTrafficLightStatus: IdtTrafficLightStatusKls

    def __init__(self):

        self.IdtTrafficLightStatus = IdtTrafficLightStatusKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
