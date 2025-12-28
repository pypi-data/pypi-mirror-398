from someip_py.codec import *


class IdtHznSegKls(SomeIpPayload):

    _include_struct_len = True

    Bridge: Uint8

    BuiltupArea: Uint8

    ComplexIntersection: Uint8

    CyclicCounter: Uint8

    DividedRoad: Uint8

    EffectiveSpdLimit: Uint16

    EffectiveSpeedLimitType: Uint8

    FormofWay: Uint8

    FunctionalRoadClass: Uint8

    MessageType: Uint8

    Numberoflanesindrivingdirection: Uint8

    NumberOfLanesInOppositeDirection: Uint8

    Offset: Uint16

    PartOfCalculatedRoute: Uint8

    PathIndex: Uint8

    RelativeProbability: Uint8

    Retransmission: Bool

    Tunnel: Uint8

    Update: Bool

    def __init__(self):

        self.Bridge = Uint8()

        self.BuiltupArea = Uint8()

        self.ComplexIntersection = Uint8()

        self.CyclicCounter = Uint8()

        self.DividedRoad = Uint8()

        self.EffectiveSpdLimit = Uint16()

        self.EffectiveSpeedLimitType = Uint8()

        self.FormofWay = Uint8()

        self.FunctionalRoadClass = Uint8()

        self.MessageType = Uint8()

        self.Numberoflanesindrivingdirection = Uint8()

        self.NumberOfLanesInOppositeDirection = Uint8()

        self.Offset = Uint16()

        self.PartOfCalculatedRoute = Uint8()

        self.PathIndex = Uint8()

        self.RelativeProbability = Uint8()

        self.Retransmission = Bool()

        self.Tunnel = Uint8()

        self.Update = Bool()


class IdtHznSeg(SomeIpPayload):

    IdtHznSeg: IdtHznSegKls

    def __init__(self):

        self.IdtHznSeg = IdtHznSegKls()
