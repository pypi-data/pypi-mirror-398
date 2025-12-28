from someip_py.codec import *


class IdtTLAMainActionKls(SomeIpPayload):

    _include_struct_len = True

    firstTurn: Uint8

    firstTurnDis: Int32

    secondTurn: Uint8

    secondTurnDis: Int32

    def __init__(self):

        self.firstTurn = Uint8()

        self.firstTurnDis = Int32()

        self.secondTurn = Uint8()

        self.secondTurnDis = Int32()


class IdtTLAMainAction(SomeIpPayload):

    IdtTLAMainAction: IdtTLAMainActionKls

    def __init__(self):

        self.IdtTLAMainAction = IdtTLAMainActionKls()
