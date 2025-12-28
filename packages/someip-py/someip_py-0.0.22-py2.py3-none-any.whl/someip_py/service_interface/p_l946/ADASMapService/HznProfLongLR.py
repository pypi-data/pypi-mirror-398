from someip_py.codec import *


class IdtHznProfLongLRKls(SomeIpPayload):

    _include_struct_len = True

    CyclicCounter: Uint8

    MessageType: Uint8

    Offset: Uint16

    PathIndex: Uint8

    ProfileType: Uint8

    Value: Uint32

    Retransmission: Bool

    Update: Bool

    ControlPoint: Bool

    def __init__(self):

        self.CyclicCounter = Uint8()

        self.MessageType = Uint8()

        self.Offset = Uint16()

        self.PathIndex = Uint8()

        self.ProfileType = Uint8()

        self.Value = Uint32()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.ControlPoint = Bool()


class IdtHznProfLongLR(SomeIpPayload):

    IdtHznProfLongLR: IdtHznProfLongLRKls

    def __init__(self):

        self.IdtHznProfLongLR = IdtHznProfLongLRKls()
