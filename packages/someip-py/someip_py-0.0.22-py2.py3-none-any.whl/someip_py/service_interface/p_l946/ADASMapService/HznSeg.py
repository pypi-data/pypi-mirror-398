from someip_py.codec import *


class IdtHznSegKls(SomeIpPayload):

    _include_struct_len = True

    CyclicCounter: Uint8

    MessageType: Uint8

    ComplexIntersection: Uint8

    FormofWay: Uint8

    FunctionalRoadClass: Uint8

    Numberoflanesindrivingdirection: Uint8

    Offset: Uint16

    PartOfCalculatedRoute: Uint8

    PathIndex: Uint8

    RelativeProbability: Uint8

    EffectiveSpdLimit: Uint16

    Bridge: Uint8

    BuiltupArea: Uint8

    DividedRoad: Uint8

    EffectiveSpeedLimitType: Uint8

    Tunnel: Uint8

    Retransmission: Bool

    Update: Bool

    NumberOfLanesInOppositeDirection: Uint8

    def __init__(self):

        self.CyclicCounter = Uint8()

        self.MessageType = Uint8()

        self.ComplexIntersection = Uint8()

        self.FormofWay = Uint8()

        self.FunctionalRoadClass = Uint8()

        self.Numberoflanesindrivingdirection = Uint8()

        self.Offset = Uint16()

        self.PartOfCalculatedRoute = Uint8()

        self.PathIndex = Uint8()

        self.RelativeProbability = Uint8()

        self.EffectiveSpdLimit = Uint16()

        self.Bridge = Uint8()

        self.BuiltupArea = Uint8()

        self.DividedRoad = Uint8()

        self.EffectiveSpeedLimitType = Uint8()

        self.Tunnel = Uint8()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.NumberOfLanesInOppositeDirection = Uint8()


class IdtHznSeg(SomeIpPayload):

    IdtHznSeg: IdtHznSegKls

    def __init__(self):

        self.IdtHznSeg = IdtHznSegKls()
