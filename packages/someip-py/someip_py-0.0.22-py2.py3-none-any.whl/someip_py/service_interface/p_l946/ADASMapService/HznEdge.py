from someip_py.codec import *


class IdtHznEdgeKls(SomeIpPayload):

    _include_struct_len = True

    CyclicCounter: Uint8

    ComplexIntersection: Uint8

    FunctionalRoadClass: Uint8

    LastStubAtOffset: Bool

    MessageType: Uint8

    NumberOfLanesInDrivingDirection: Uint8

    EdgeOffset: Uint16

    PartOfCalculatedRoute: Uint8

    PathIndex: Uint8

    RelativeProbability: Uint8

    RightofWay: Uint8

    TurnAngle: Uint8

    Retransmission: Bool

    Update: Bool

    FormOfWay: Uint8

    NumberOfLanesInOppositeDirection: Uint8

    SubPathIndex: Uint8

    def __init__(self):

        self.CyclicCounter = Uint8()

        self.ComplexIntersection = Uint8()

        self.FunctionalRoadClass = Uint8()

        self.LastStubAtOffset = Bool()

        self.MessageType = Uint8()

        self.NumberOfLanesInDrivingDirection = Uint8()

        self.EdgeOffset = Uint16()

        self.PartOfCalculatedRoute = Uint8()

        self.PathIndex = Uint8()

        self.RelativeProbability = Uint8()

        self.RightofWay = Uint8()

        self.TurnAngle = Uint8()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.FormOfWay = Uint8()

        self.NumberOfLanesInOppositeDirection = Uint8()

        self.SubPathIndex = Uint8()


class IdtHznEdge(SomeIpPayload):

    IdtHznEdge: IdtHznEdgeKls

    def __init__(self):

        self.IdtHznEdge = IdtHznEdgeKls()
