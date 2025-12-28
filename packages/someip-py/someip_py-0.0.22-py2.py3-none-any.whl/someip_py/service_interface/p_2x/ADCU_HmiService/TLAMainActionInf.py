from someip_py.codec import *


class TimeAndDist(SomeIpPayload):

    RemainTime: Uint32

    RemainDist: Uint32

    def __init__(self):

        self.RemainTime = Uint32()

        self.RemainDist = Uint32()


class IdtTLAMainActionKls(SomeIpPayload):
    _has_dynamic_size = True

    FirstTurn: Uint8

    FirstTurnDis: Int32

    SecondTurn: Uint8

    SecondTurnDis: Int32

    PathIDSeN: Uint32

    CurSegIdxSeN: Int32

    CurLinkIdxSeN: Int32

    LinkRemainDistSeN: Int32

    CurrRoadNameNavingSeN: SomeIpDynamicSizeString

    RoadLevelForNavingSeN: Int32

    CrossOutCntSeN: Uint8

    RouteRemain: TimeAndDist

    ViaRemain: SomeIpDynamicSizeArray[TimeAndDist]

    ChargeStationRemain: SomeIpDynamicSizeArray[TimeAndDist]

    RoundaboutOutAngle: Uint32

    CurLinkSpeed: Uint32

    def __init__(self):

        self.FirstTurn = Uint8()

        self.FirstTurnDis = Int32()

        self.SecondTurn = Uint8()

        self.SecondTurnDis = Int32()

        self.PathIDSeN = Uint32()

        self.CurSegIdxSeN = Int32()

        self.CurLinkIdxSeN = Int32()

        self.LinkRemainDistSeN = Int32()

        self.CurrRoadNameNavingSeN = SomeIpDynamicSizeString()

        self.RoadLevelForNavingSeN = Int32()

        self.CrossOutCntSeN = Uint8()

        self.RouteRemain = TimeAndDist()

        self.ViaRemain = SomeIpDynamicSizeArray(TimeAndDist)

        self.ChargeStationRemain = SomeIpDynamicSizeArray(TimeAndDist)

        self.RoundaboutOutAngle = Uint32()

        self.CurLinkSpeed = Uint32()


class IdtTLAMainAction(SomeIpPayload):

    IdtTLAMainAction: IdtTLAMainActionKls

    def __init__(self):

        self.IdtTLAMainAction = IdtTLAMainActionKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
