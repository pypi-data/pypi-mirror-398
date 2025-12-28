from someip_py.codec import *


class PathPoint(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    ParkingLinePointTheta: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()

        self.ParkingLinePointTheta = Int32()


class PlanningTrajectorystopline(SomeIpPayload):

    PlanningTrajectorystopline: SomeIpDynamicSizeArray[PathPoint]

    def __init__(self):

        self.PlanningTrajectorystopline = SomeIpDynamicSizeArray(PathPoint)
