from someip_py.codec import *


class IdtAVPMapGenerateStatusKls(SomeIpPayload):

    MapId: Uint64

    MapGenerateStatus: Uint8

    MapGeneratePercentage: Uint8

    MappingMileage: Float32

    MapFloorNum: Uint8

    MapSlotNum: Uint16

    def __init__(self):

        self.MapId = Uint64()

        self.MapGenerateStatus = Uint8()

        self.MapGeneratePercentage = Uint8()

        self.MappingMileage = Float32()

        self.MapFloorNum = Uint8()

        self.MapSlotNum = Uint16()


class IdtAVPMapGenerateStatus(SomeIpPayload):

    IdtAVPMapGenerateStatus: IdtAVPMapGenerateStatusKls

    def __init__(self):

        self.IdtAVPMapGenerateStatus = IdtAVPMapGenerateStatusKls()
