from someip_py.codec import *


class ObstacleObject(SomeIpPayload):

    PointX: Float32

    PointY: Float32

    ObstacleDistance: Float32

    ObstacleGroupIndex: Uint16

    ObstacleFlag: Uint8

    def __init__(self):

        self.PointX = Float32()

        self.PointY = Float32()

        self.ObstacleDistance = Float32()

        self.ObstacleGroupIndex = Uint16()

        self.ObstacleFlag = Uint8()


class IdtPDCWarningInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    ObsMiniDistanceFrntMinSeN: Float32

    ObsMiniDistanceReMinSeN: Float32

    ObsMiniFrntStopDispSeN: Uint8

    ObsMiniReStopDispSeN: Uint8

    ObsMiniFrntMinDstSeN: Uint8

    ObsMiniReMinDstSeN: Uint8

    AudWarnOfSnsrParkAssiFrntSeN: Uint8

    AudWarnOfSnsrParkAssiReSeN: Uint8

    ObstacleNumSeN: Uint16

    ObstacleObjectSeN: SomeIpDynamicSizeArray[ObstacleObject]

    ReservedSeN: SomeIpDynamicSizeArray[Float32]

    FusionPDCAvailableFlag: Uint8

    FusionPDCAvailableIndexSeN: Uint32

    RearDoorOpenInhibitSeN: Uint8

    def __init__(self):

        self.ObsMiniDistanceFrntMinSeN = Float32()

        self.ObsMiniDistanceReMinSeN = Float32()

        self.ObsMiniFrntStopDispSeN = Uint8()

        self.ObsMiniReStopDispSeN = Uint8()

        self.ObsMiniFrntMinDstSeN = Uint8()

        self.ObsMiniReMinDstSeN = Uint8()

        self.AudWarnOfSnsrParkAssiFrntSeN = Uint8()

        self.AudWarnOfSnsrParkAssiReSeN = Uint8()

        self.ObstacleNumSeN = Uint16()

        self.ObstacleObjectSeN = SomeIpDynamicSizeArray(ObstacleObject)

        self.ReservedSeN = SomeIpDynamicSizeArray(Float32)

        self.FusionPDCAvailableFlag = Uint8()

        self.FusionPDCAvailableIndexSeN = Uint32()

        self.RearDoorOpenInhibitSeN = Uint8()


class IdtPDCWarningInfo(SomeIpPayload):

    IdtPDCWarningInfo: IdtPDCWarningInfoKls

    def __init__(self):

        self.IdtPDCWarningInfo = IdtPDCWarningInfoKls()
