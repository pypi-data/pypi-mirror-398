from someip_py.codec import *


class IdtHznProfLongKls(SomeIpPayload):

    _include_struct_len = True

    ControlPoint: Bool

    CyclicCounter: Uint8

    MessageType: Uint8

    Offset: Uint16

    PathIndex: Uint8

    ProfileType: Uint8

    Retransmission: Bool

    Update: Bool

    Value: Uint32

    def __init__(self):

        self.ControlPoint = Bool()

        self.CyclicCounter = Uint8()

        self.MessageType = Uint8()

        self.Offset = Uint16()

        self.PathIndex = Uint8()

        self.ProfileType = Uint8()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.Value = Uint32()


class IdtHznProfLong(SomeIpPayload):

    IdtHznProfLong: IdtHznProfLongKls

    def __init__(self):

        self.IdtHznProfLong = IdtHznProfLongKls()
