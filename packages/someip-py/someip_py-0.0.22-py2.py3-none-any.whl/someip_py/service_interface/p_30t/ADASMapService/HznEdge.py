from someip_py.codec import *


class IdtHznEdgeKls(SomeIpPayload):

    _include_struct_len = True

    ComplexIntersection: Uint8

    CyclicCounter: Uint8

    FormOfWay: Uint8

    FunctionalRoadClass: Uint8

    LastStubAtOffset: Bool

    MessageType: Uint8

    NumberOfLanesInDrivingDirection: Uint8

    NumberOfLanesInOppositeDirection: Uint8

    EdgeOffset: Uint16

    PartOfCalculatedRoute: Uint8

    PathIndex: Uint8

    RelativeProbability: Uint8

    Retransmission: Bool

    RightofWay: Uint8

    SubPathIndex: Uint8

    TurnAngle: Uint8

    Update: Bool

    def __init__(self):

        self.ComplexIntersection = Uint8()

        self.CyclicCounter = Uint8()

        self.FormOfWay = Uint8()

        self.FunctionalRoadClass = Uint8()

        self.LastStubAtOffset = Bool()

        self.MessageType = Uint8()

        self.NumberOfLanesInDrivingDirection = Uint8()

        self.NumberOfLanesInOppositeDirection = Uint8()

        self.EdgeOffset = Uint16()

        self.PartOfCalculatedRoute = Uint8()

        self.PathIndex = Uint8()

        self.RelativeProbability = Uint8()

        self.Retransmission = Bool()

        self.RightofWay = Uint8()

        self.SubPathIndex = Uint8()

        self.TurnAngle = Uint8()

        self.Update = Bool()


class IdtHznEdge(SomeIpPayload):

    IdtHznEdge: IdtHznEdgeKls

    def __init__(self):

        self.IdtHznEdge = IdtHznEdgeKls()
