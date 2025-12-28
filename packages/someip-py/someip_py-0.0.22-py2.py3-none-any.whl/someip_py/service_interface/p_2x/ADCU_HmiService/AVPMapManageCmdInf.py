from someip_py.codec import *


class CoordinateSys(SomeIpPayload):

    CoordinateXSeN: Int32

    CoordinateYSeN: Int32

    CoordinateZSeN: Int32

    def __init__(self):

        self.CoordinateXSeN = Int32()

        self.CoordinateYSeN = Int32()

        self.CoordinateZSeN = Int32()


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class AVPCollectedDestination(SomeIpPayload):

    CollectedDestinationType: Uint8

    CollectedDestinationSlotId: Uint32

    CollectedDestinationPoint: CoordinateSys

    CollectedDestinationFloorLevel: Int8

    CollectedDestinationPOIID: Uint32

    CollectedDestinationPriority: Uint8

    CollectedParkMapId: Uint64

    CollectedDestinationName: SomeIpDynamicSizeString

    CollectedDestinationLabel: SomeIpDynamicSizeString

    DestinationType: Uint8

    DestinationEditType: Uint8

    GlobalLocation: Pos2D

    def __init__(self):

        self.CollectedDestinationType = Uint8()

        self.CollectedDestinationSlotId = Uint32()

        self.CollectedDestinationPoint = CoordinateSys()

        self.CollectedDestinationFloorLevel = Int8()

        self.CollectedDestinationPOIID = Uint32()

        self.CollectedDestinationPriority = Uint8()

        self.CollectedParkMapId = Uint64()

        self.CollectedDestinationName = SomeIpDynamicSizeString()

        self.CollectedDestinationLabel = SomeIpDynamicSizeString()

        self.DestinationType = Uint8()

        self.DestinationEditType = Uint8()

        self.GlobalLocation = Pos2D()


class AVPCollectedMap(SomeIpPayload):
    _has_dynamic_size = True

    MapId: Uint64

    MapName: SomeIpDynamicSizeString

    DestinationNum: Uint32

    DestinationList: SomeIpDynamicSizeArray[AVPCollectedDestination]

    MapLearningTime: Uint64

    MapType: Uint8

    MapCollectPin: Uint8

    MapStatus: Uint8

    MapErrorCode: Uint8

    def __init__(self):

        self.MapId = Uint64()

        self.MapName = SomeIpDynamicSizeString()

        self.DestinationNum = Uint32()

        self.DestinationList = SomeIpDynamicSizeArray(AVPCollectedDestination)

        self.MapLearningTime = Uint64()

        self.MapType = Uint8()

        self.MapCollectPin = Uint8()

        self.MapStatus = Uint8()

        self.MapErrorCode = Uint8()


class IdtAVPMapManageCmdKls(SomeIpPayload):
    _has_dynamic_size = True

    MapManageCmdTypeSeN: Uint8

    MapUpdateInfoSeN: SomeIpDynamicSizeArray[AVPCollectedMap]

    MapDeleteCmdSeN: SomeIpDynamicSizeArray[Uint32]

    DestinationUpdateInfoSeN: SomeIpDynamicSizeArray[AVPCollectedDestination]

    DestinationDeleteCmdSeN: SomeIpDynamicSizeArray[Uint32]

    DestinationTypeDeleteCmdSeN: Uint8

    def __init__(self):

        self.MapManageCmdTypeSeN = Uint8()

        self.MapUpdateInfoSeN = SomeIpDynamicSizeArray(AVPCollectedMap)

        self.MapDeleteCmdSeN = SomeIpDynamicSizeArray(Uint32)

        self.DestinationUpdateInfoSeN = SomeIpDynamicSizeArray(AVPCollectedDestination)

        self.DestinationDeleteCmdSeN = SomeIpDynamicSizeArray(Uint32)

        self.DestinationTypeDeleteCmdSeN = Uint8()


class IdtAVPMapManageCmd(SomeIpPayload):

    IdtAVPMapManageCmd: IdtAVPMapManageCmdKls

    def __init__(self):

        self.IdtAVPMapManageCmd = IdtAVPMapManageCmdKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
