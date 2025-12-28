from someip_py.codec import *


class IdtHznPosnKls(SomeIpPayload):

    _include_struct_len = True

    CyclicCounter: Uint8

    MessageType: Uint8

    Offset: Uint16

    PathIndex: Uint8

    PositionProbability: Uint8

    RelativeHeading: Uint8

    CurrentLane: Uint8

    PositionAge: Uint16

    PositionConfidence: Uint8

    Speed: Uint16

    PositionIndex: Uint8

    def __init__(self):

        self.CyclicCounter = Uint8()

        self.MessageType = Uint8()

        self.Offset = Uint16()

        self.PathIndex = Uint8()

        self.PositionProbability = Uint8()

        self.RelativeHeading = Uint8()

        self.CurrentLane = Uint8()

        self.PositionAge = Uint16()

        self.PositionConfidence = Uint8()

        self.Speed = Uint16()

        self.PositionIndex = Uint8()


class IdtHznPosn(SomeIpPayload):

    IdtHznPosn: IdtHznPosnKls

    def __init__(self):

        self.IdtHznPosn = IdtHznPosnKls()
