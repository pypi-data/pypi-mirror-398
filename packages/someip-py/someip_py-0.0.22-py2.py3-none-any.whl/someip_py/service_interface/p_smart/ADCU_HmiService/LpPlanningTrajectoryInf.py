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


class LpPlanningTrajectoryKls(SomeIpPayload):
    _has_dynamic_size = True

    LpPathPointsSeN: SomeIpDynamicSizeArray[LPPathPoint]

    def __init__(self):

        self.LpPathPointsSeN = SomeIpDynamicSizeArray(LPPathPoint)


class LpPlanningTrajectory(SomeIpPayload):

    LpPlanningTrajectory: LpPlanningTrajectoryKls

    def __init__(self):

        self.LpPlanningTrajectory = LpPlanningTrajectoryKls()
