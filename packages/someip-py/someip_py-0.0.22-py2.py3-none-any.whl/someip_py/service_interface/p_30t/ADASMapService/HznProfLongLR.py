from someip_py.codec import *


class IdtHznProfLongLRKls(SomeIpPayload):

    _include_struct_len = True

    MessageType: Uint8

    CyclicCounter: Uint8

    Retransmission: Bool

    PathIndex: Uint8

    Offset: Uint16

    Update: Bool

    ProfileType: Uint8

    ControlPoint: Bool

    Value: Uint32

    def __init__(self):

        self.MessageType = Uint8()

        self.CyclicCounter = Uint8()

        self.Retransmission = Bool()

        self.PathIndex = Uint8()

        self.Offset = Uint16()

        self.Update = Bool()

        self.ProfileType = Uint8()

        self.ControlPoint = Bool()

        self.Value = Uint32()


class IdtHznProfLongLR(SomeIpPayload):

    IdtHznProfLongLR: IdtHznProfLongLRKls

    def __init__(self):

        self.IdtHznProfLongLR = IdtHznProfLongLRKls()
