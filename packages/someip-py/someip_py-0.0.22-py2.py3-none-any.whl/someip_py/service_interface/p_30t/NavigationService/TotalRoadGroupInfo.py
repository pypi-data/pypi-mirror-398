from someip_py.codec import *


class IdtRoadGroupInformation(SomeIpPayload):

    _include_struct_len = True

    RoadNumber: Uint8

    RoadCongestionLevel: Uint8

    RoadDistance: Uint32

    RoadPercent: Float32

    RoadTraveltime: Uint64

    def __init__(self):

        self.RoadNumber = Uint8()

        self.RoadCongestionLevel = Uint8()

        self.RoadDistance = Uint32()

        self.RoadPercent = Float32()

        self.RoadTraveltime = Uint64()


class IdtTotalGroupInformation(SomeIpPayload):

    IdtTotalGroupInformation: SomeIpDynamicSizeArray[IdtRoadGroupInformation]

    def __init__(self):

        self.IdtTotalGroupInformation = SomeIpDynamicSizeArray(IdtRoadGroupInformation)
