from someip_py.codec import *


class LPPathPoint(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    PositionZSeN: Int32

    ParkingLinePointTheta: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()

        self.PositionZSeN = Int32()

        self.ParkingLinePointTheta = Int32()


class LPTime(SomeIpPayload):

    minute: Uint16

    second: Uint16

    def __init__(self):

        self.minute = Uint16()

        self.second = Uint16()


class LpPathInfoKls(SomeIpPayload):

    PathIDSeN: Uint32

    PathTotalDistanceSeN: Uint16

    TargetSlot: Uint32

    PathSurplusDistanceSeN: Uint16

    PathStartPointSeN: LPPathPoint

    PathTerminalPointSeN: LPPathPoint

    LpTimeSeN: LPTime

    LpDistanceSeN: Uint16

    LpLongitudeSeN: Float64

    LpLatitudeSeN: Float64

    LpParkInTrajReDistanceSeN: Uint16

    LpParkInTrajAlDistanceSeN: Uint16

    def __init__(self):

        self.PathIDSeN = Uint32()

        self.PathTotalDistanceSeN = Uint16()

        self.TargetSlot = Uint32()

        self.PathSurplusDistanceSeN = Uint16()

        self.PathStartPointSeN = LPPathPoint()

        self.PathTerminalPointSeN = LPPathPoint()

        self.LpTimeSeN = LPTime()

        self.LpDistanceSeN = Uint16()

        self.LpLongitudeSeN = Float64()

        self.LpLatitudeSeN = Float64()

        self.LpParkInTrajReDistanceSeN = Uint16()

        self.LpParkInTrajAlDistanceSeN = Uint16()


class LpPathInfo(SomeIpPayload):

    LpPathInfo: LpPathInfoKls

    def __init__(self):

        self.LpPathInfo = LpPathInfoKls()
