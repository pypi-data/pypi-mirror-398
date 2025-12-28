from someip_py.codec import *


class IdtTrafficLightStatusKls(SomeIpPayload):

    _include_struct_len = True

    crossManeuverID: Uint8

    TrafficLightTime: Uint16

    TrafficLightStatus: Uint8

    WaitRountCount: Uint8

    def __init__(self):

        self.crossManeuverID = Uint8()

        self.TrafficLightTime = Uint16()

        self.TrafficLightStatus = Uint8()

        self.WaitRountCount = Uint8()


class IdtTrafficLightStatus(SomeIpPayload):

    IdtTrafficLightStatus: IdtTrafficLightStatusKls

    def __init__(self):

        self.IdtTrafficLightStatus = IdtTrafficLightStatusKls()
