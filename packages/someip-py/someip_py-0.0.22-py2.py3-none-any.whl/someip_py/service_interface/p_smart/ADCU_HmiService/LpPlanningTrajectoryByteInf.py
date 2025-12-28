from someip_py.codec import *


class LpPlanningTrajectoryByteKls(SomeIpPayload):
    _has_dynamic_size = True

    LpPathPointsSeN1: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.LpPathPointsSeN1 = SomeIpDynamicSizeArray(Uint8)


class LpPlanningTrajectoryByte(SomeIpPayload):

    LpPlanningTrajectoryByte: LpPlanningTrajectoryByteKls

    def __init__(self):

        self.LpPlanningTrajectoryByte = LpPlanningTrajectoryByteKls()
