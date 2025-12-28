from someip_py.codec import *


class IdtHznPosnLRKls(SomeIpPayload):

    _include_struct_len = True

    MessageType: Uint8

    CyclicCounter: Uint8

    PathIndex: Uint8

    Offset: Uint16

    PositionIndex: Uint8

    PositionAge: Uint16

    Speed: Uint16

    RelativeHeading: Uint8

    PositionProbability: Uint8

    PositionConfidence: Uint8

    CurrentLane: Uint8

    def __init__(self):

        self.MessageType = Uint8()

        self.CyclicCounter = Uint8()

        self.PathIndex = Uint8()

        self.Offset = Uint16()

        self.PositionIndex = Uint8()

        self.PositionAge = Uint16()

        self.Speed = Uint16()

        self.RelativeHeading = Uint8()

        self.PositionProbability = Uint8()

        self.PositionConfidence = Uint8()

        self.CurrentLane = Uint8()


class IdtHznPosnLR(SomeIpPayload):

    IdtHznPosnLR: IdtHznPosnLRKls

    def __init__(self):

        self.IdtHznPosnLR = IdtHznPosnLRKls()
